import numpy as np

# -------------------------
# Utilidades de impresión
# -------------------------
def print_tableau_simple(tableau, basic_vars, var_names, title=""):
    rows, cols = tableau.shape
    print("\n" + "="*70)
    print(title)
    print("="*70)
    header = ["BV"] + var_names + ["bi"]
    print(" | ".join(f"{h:>8}" for h in header))
    print("-" * 70)
    for i in range(rows):
        row = tableau[i]
        print(f"{basic_vars[i]:>8} | " + " | ".join(f"{val:>8.3f}" for val in row))
    print("-" * 70)

def tableau_to_dict(tableau, basic_vars, var_names, zjc=None, phase=1, iteration=0):
    """
    Convierte un tableau a un diccionario para enviar al frontend
    """
    rows, cols = tableau.shape
    
    # Crear encabezados
    headers = ["VB"] + var_names + ["LD"]
    
    # Crear filas
    data = []
    for i in range(rows):
        row_data = [basic_vars[i] if i < len(basic_vars) else f"R{i+1}"]
        row_data.extend([float(val) for val in tableau[i]])
        data.append(row_data)
    
    # Agregar fila Zj-Cj si está disponible
    if zjc is not None:
        zj_row = ["Zj-Cj"]
        zj_row.extend([float(val) for val in zjc])
        data.append(zj_row)
    
    return {
        "phase": phase,
        "iteration": iteration,
        "headers": headers,
        "data": data,
        "variables": var_names,
        "basic_vars": basic_vars
    }


# -------------------------
# Construir tableau inicial
# -------------------------
def build_initial_tableau(A, b):
    A = np.asarray(A, dtype=float)
    b = np.asarray(b, dtype=float)
    m, n = A.shape
    tableau = np.zeros((m, n + 1), dtype=float)
    tableau[:, :-1] = A
    tableau[:, -1] = b
    return tableau


# -------------------------
# Calcular Zj y Zj-Cj
# -------------------------
def compute_zj_zjc(tableau, basic_costs, c):
    m, n_plus1 = tableau.shape
    n = n_plus1 - 1
    zj = np.zeros(n_plus1, dtype=float)
    for i in range(m):
        zj += basic_costs[i] * tableau[i]
    c_full = np.concatenate([np.asarray(c, dtype=float), [0.0]])
    zjc = zj - c_full
    return zj, zjc


# -------------------------
# Elegir pivote (según tu regla)
# -------------------------
def choose_pivot_custom(tableau, zjc, maximize=False, tol=1e-12):
    n_plus1 = tableau.shape[1]
    n = n_plus1 - 1
    zjc_vars = zjc[:-1]

    if not maximize:
        candidates = [j for j, val in enumerate(zjc_vars) if val > tol]
        if not candidates:
            return None, None, 'optimal'
        pivot_col = max(candidates, key=lambda j: zjc_vars[j])
    else:
        candidates = [j for j, val in enumerate(zjc_vars) if val < -tol]
        if not candidates:
            return None, None, 'optimal'
        pivot_col = min(candidates, key=lambda j: zjc_vars[j])

    col_vec = tableau[:, pivot_col]
    bi = tableau[:, -1]
    ratios = []
    for i in range(len(col_vec)):
        if col_vec[i] > tol:
            ratios.append((bi[i] / col_vec[i], i))
    if not ratios:
        return None, None, 'unbounded'
    pivot_row = min(ratios, key=lambda x: x[0])[1]
    return pivot_row, pivot_col, 'ok'


# -------------------------
# Operación pivote
# -------------------------
def pivot_transform(tableau, pivot_row, pivot_col, tol=1e-12):
    A = tableau.copy()
    pivot_val = A[pivot_row, pivot_col]
    if abs(pivot_val) < tol:
        raise ValueError("Pivote ~ 0, abortando para evitar NaN.")
    A[pivot_row, :] = A[pivot_row, :] / pivot_val
    for i in range(A.shape[0]):
        if i == pivot_row:
            continue
        A[i, :] = A[i, :] - A[i, pivot_col] * A[pivot_row, :]
    return A


# -------------------------
# Método de 2 fases (MODIFICADO para capturar tablas)
# -------------------------
def two_phase_method_fixed(A, b, c_final, var_names, basic_vars_init, basic_costs_init, artificial_indices, mode=0):
    """
    MODIFICADO: Ahora retorna también las tablas del proceso
    """
    tableau = build_initial_tableau(A, b)
    m, n_plus1 = tableau.shape
    n = n_plus1 - 1

    # Lista para almacenar todas las tablas
    all_tables = []

    basic_vars = basic_vars_init[:]
    Cb = np.array(basic_costs_init, dtype=float)

    # Tabla inicial Fase 1
    print("\n=== FASE 1 (tabla inicial) ===")
    print_tableau_simple(tableau, basic_vars, var_names, title="Tableau inicial Fase 1")
    
    # Guardar tabla inicial
    zj, zjc = compute_zj_zjc(tableau, Cb, np.zeros(n))
    table_dict = tableau_to_dict(tableau, basic_vars, var_names, zjc, phase=1, iteration=0)
    table_dict["title"] = "Tabla Inicial - Fase 1"
    all_tables.append(table_dict)

    # Construir c_phase1 según mode
    c_phase1 = np.zeros(n, dtype=float)
    sign = 1.0 if mode == 0 else -1.0
    for idx in artificial_indices:
        if 0 <= idx < n:
            c_phase1[idx] = sign
        else:
            raise IndexError(f"Índice artificial {idx} fuera de rango (n={n}).")

    # FASE 1
    iter_count = 0
    max_iter = 200
    phase1_tables = []
    
    while True:
        iter_count += 1
        if iter_count > max_iter:
            raise RuntimeError("Máximo iteraciones en Fase 1 alcanzado.")

        zj, zjc = compute_zj_zjc(tableau, Cb, c_phase1)
        
        # Guardar tabla antes del pivote
        table_dict = tableau_to_dict(tableau, basic_vars, var_names, zjc, phase=1, iteration=iter_count)
        table_dict["title"] = f"Iteración {iter_count} - Fase 1"
        table_dict["zj_cj"] = [float(val) for val in zjc]
        table_dict["pivot_info"] = None
        all_tables.append(table_dict)
        phase1_tables.append(table_dict)
        
        print("   Zj-Cj | " + " | ".join(f"{val:>8.3f}" for val in zjc))
        
        pivot_row, pivot_col, status = choose_pivot_custom(tableau, zjc, maximize=(mode==1))
        
        # Actualizar información del pivote en la última tabla
        if pivot_row is not None and pivot_col is not None:
            all_tables[-1]["pivot_info"] = {
                "row": int(pivot_row),
                "col": int(pivot_col),
                "entra": var_names[pivot_col],
                "sale": basic_vars[pivot_row] if pivot_row < len(basic_vars) else f"R{pivot_row+1}"
            }
        
        if status == 'optimal':
            print("Fase 1: óptimo alcanzado.")
            break
        if status == 'unbounded':
            print("Fase 1: no hay pivote válido.")
            return None, None, all_tables

        print(f"Pivot (F1): columna = {var_names[pivot_col]}, fila = {pivot_row+1}")
        basic_vars[pivot_row] = var_names[pivot_col]
        Cb[pivot_row] = c_phase1[pivot_col]

        tableau = pivot_transform(tableau, pivot_row, pivot_col)
        print_tableau_simple(tableau, basic_vars, var_names, title=f"Después de pivote F1 (iter {iter_count})")

    zj_final, zjc_final = compute_zj_zjc(tableau, Cb, c_phase1)
    W_val = zj_final[-1]
    print(f"Valor de W (suma artificiales) = {W_val:.6f}")
    
    # Guardar tabla final de Fase 1
    table_dict = tableau_to_dict(tableau, basic_vars, var_names, zjc_final, phase=1, iteration=iter_count+1)
    table_dict["title"] = "Tabla Final - Fase 1"
    table_dict["W_value"] = float(W_val)
    all_tables.append(table_dict)
    
    if abs(W_val) > 1e-8:
        print("PROBLEMA INFACTIBLE en Fase 1 (W != 0).")
        return None, None, all_tables

    # Eliminar artificiales básicas
    art_set = set(artificial_indices)
    for row_idx in range(m):
        if basic_vars[row_idx] in var_names:
            col_idx = var_names.index(basic_vars[row_idx])
            if col_idx in art_set:
                found = False
                for j in range(n):
                    if j in art_set:
                        continue
                    if abs(tableau[row_idx, j]) > 1e-12:
                        print(f"Eliminando artificial {basic_vars[row_idx]}")
                        basic_vars[row_idx] = var_names[j]
                        Cb[row_idx] = 0.0
                        tableau = pivot_transform(tableau, row_idx, j)
                        print_tableau_simple(tableau, basic_vars, var_names, title="Después de pivot para eliminar artificial")
                        
                        # Guardar tabla después de eliminar artificial
                        zj_temp, zjc_temp = compute_zj_zjc(tableau, Cb, c_phase1)
                        table_dict = tableau_to_dict(tableau, basic_vars, var_names, zjc_temp, phase=1.5, iteration=0)
                        table_dict["title"] = f"Eliminación artificial - Fila {row_idx+1}"
                        all_tables.append(table_dict)
                        
                        found = True
                        break
                if not found:
                    print(f"WARNING: no se pudo eliminar la artificial básica {basic_vars[row_idx]}")

    # Preparar Fase 2
    keep_cols = [j for j in range(n) if j not in art_set]
    new_tableau = np.zeros((m, len(keep_cols) + 1), dtype=float)
    for i, j in enumerate(keep_cols):
        new_tableau[:, i] = tableau[:, j]
    new_tableau[:, -1] = tableau[:, -1]

    new_var_names = [var_names[j] for j in keep_cols]
    new_c_final = [c_final[j] for j in keep_cols]

    for i in range(m):
        bv = basic_vars[i]
        if bv in var_names and var_names.index(bv) in art_set:
            basic_vars[i] = "R" + str(i+1)

    Cb2 = np.zeros(m, dtype=float)
    for i in range(m):
        bv = basic_vars[i]
        if bv in new_var_names:
            idx_new = new_var_names.index(bv)
            Cb2[i] = new_c_final[idx_new]
        else:
            Cb2[i] = 0.0

    print("\n=== PREPARADA FASE 2 ===")
    print_tableau_simple(new_tableau, basic_vars, new_var_names, title="Tableau inicial Fase 2")

    # Guardar tabla inicial Fase 2
    zj_init_f2, zjc_init_f2 = compute_zj_zjc(new_tableau, Cb2, new_c_final)
    table_dict = tableau_to_dict(new_tableau, basic_vars, new_var_names, zjc_init_f2, phase=2, iteration=0)
    table_dict["title"] = "Tabla Inicial - Fase 2"
    all_tables.append(table_dict)

    # FASE 2
    tableau = new_tableau
    var_names = new_var_names
    c_final = new_c_final
    Cb = Cb2
    n = len(var_names)

    iter_count = 0
    while True:
        iter_count += 1
        if iter_count > max_iter:
            raise RuntimeError("Máximo iteraciones en Fase 2 alcanzado.")

        zj, zjc = compute_zj_zjc(tableau, Cb, c_final)
        
        # Guardar tabla antes del pivote
        table_dict = tableau_to_dict(tableau, basic_vars, var_names, zjc, phase=2, iteration=iter_count)
        table_dict["title"] = f"Iteración {iter_count} - Fase 2"
        table_dict["zj_cj"] = [float(val) for val in zjc]
        table_dict["pivot_info"] = None
        all_tables.append(table_dict)
        
        print("   Zj-Cj | " + " | ".join(f"{val:>8.3f}" for val in zjc))
        
        pivot_row, pivot_col, status = choose_pivot_custom(tableau, zjc, maximize=(mode==1))
        
        # Actualizar información del pivote
        if pivot_row is not None and pivot_col is not None:
            all_tables[-1]["pivot_info"] = {
                "row": int(pivot_row),
                "col": int(pivot_col),
                "entra": var_names[pivot_col],
                "sale": basic_vars[pivot_row] if pivot_row < len(basic_vars) else f"R{pivot_row+1}"
            }
        
        if status == 'optimal':
            print("Fase 2: óptimo alcanzado.")
            break
        if status == 'unbounded':
            print("Fase 2: no hay pivote válido.")
            return None, None, all_tables

        print(f"Pivot (F2): columna = {var_names[pivot_col]}, fila = {pivot_row+1}")
        basic_vars[pivot_row] = var_names[pivot_col]
        Cb[pivot_row] = c_final[pivot_col]

        tableau = pivot_transform(tableau, pivot_row, pivot_col)
        print_tableau_simple(tableau, basic_vars, var_names, title=f"Después de pivote F2 (iter {iter_count})")

    # Solución final
    solution = {name: 0.0 for name in var_names}
    for i in range(m):
        bv = basic_vars[i]
        if bv in var_names:
            solution[bv] = tableau[i, -1]

    zj_final2, _ = compute_zj_zjc(tableau, Cb, c_final)
    Z_opt = zj_final2[-1]
    
    # Guardar tabla final
    zj_last, zjc_last = compute_zj_zjc(tableau, Cb, c_final)
    table_dict = tableau_to_dict(tableau, basic_vars, var_names, zjc_last, phase=2, iteration=iter_count+1)
    table_dict["title"] = "Tabla Final - Solución Óptima"
    table_dict["Z_value"] = float(Z_opt)
    all_tables.append(table_dict)
    
    return solution, Z_opt, all_tables