from flask import Flask, render_template, request, jsonify
from backend.Grafico import calcular_region_factible
from backend.Doblefase import two_phase_method_fixed
import numpy as np
import os

app = Flask(__name__, template_folder='frontend', static_folder='frontend')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/resolver', methods=['POST'])
def resolver():
    data = request.json
    
    metodo = data.get('metodo', 'grafico')
    contador_variables = int(data.get('variables', 2))
    coeficientes = data.get('coeficientes', [])
    tipo = data.get('tipo', 'max')
    restricciones_data = data.get('restricciones', [])
    
    # Convertir tipo a modo para doble fase
    mode = 0 if tipo == 'min' else 1  # 0=minimización, 1=maximización
    
    if metodo == 'grafico':
        # Método Gráfico - solo funciona con 2 variables
        if contador_variables != 2:
            return jsonify({
                "error": "El método gráfico solo funciona con 2 variables",
                "tipo": tipo
            }), 400
        
        p = float(coeficientes[0]) if len(coeficientes) > 0 else 0.1
        q = float(coeficientes[1]) if len(coeficientes) > 1 else 0.08
        
        # Obtener restricciones
        restricciones = []
        for restriccion in restricciones_data:
            coefs = restriccion['coeficientes']
            if len(coefs) != 2:
                return jsonify({
                    "error": "El método gráfico requiere exactamente 2 variables por restricción",
                    "tipo": tipo
                }), 400
            a = float(coefs[0])
            b = float(coefs[1])
            c = float(restriccion['c'])
            signo = restriccion['signo']
            
            # Convertir ≥ a ≤ multiplicando por -1
            if signo == 'geq':
                a = -a
                b = -b
                c = -c
            # Ignorar = para método gráfico, tratarlo como ≤
            elif signo == 'eq':
                pass
            
            restricciones.append((a, b, c))
        
        # Calcular usando el método gráfico
        try:
            resultado = calcular_region_factible(restricciones, (p, q, tipo))
            resultado["tipo"] = tipo
            return jsonify(resultado)
        except Exception as e:
            return jsonify({
                "error": str(e),
                "tipo": tipo
            }), 400
    
    elif metodo == 'doblefase':
        # Método Doble Fase - CORREGIDO
        try:
            m = len(restricciones_data)  # Número de restricciones
            n = contador_variables  # Número de variables originales
            
            print(f"\n=== CONSTRUYENDO PROBLEMA DOBLE FASE ===")
            print(f"Variables originales: {n}")
            print(f"Restricciones: {m}")
            print(f"Tipo: {tipo} (mode={mode})")
            
            # ==============================================
            # 1. CONTAR VARIABLES ADICIONALES CORRECTAMENTE
            # ==============================================
            slack_count = 0      # Variables de holgura (≤)
            excess_count = 0     # Variables de exceso (≥)
            artificial_count = 0 # Variables artificiales (≥ y =)
            
            for i, restriccion in enumerate(restricciones_data):
                signo = restriccion['signo']
                print(f"R{i+1}: signo={signo}")
                
                if signo == 'leq':
                    slack_count += 1
                elif signo == 'geq':
                    excess_count += 1
                    artificial_count += 1
                elif signo == 'eq':
                    artificial_count += 1
            
            total_vars = n + slack_count + excess_count + artificial_count
            print(f"Variables totales: {total_vars} (x:{n}, s:{slack_count}, e:{excess_count}, A:{artificial_count})")
            
            # ==============================================
            # 2. CONSTRUIR MATRIZ A CORRECTAMENTE
            # ==============================================
            A = np.zeros((m, total_vars), dtype=float)
            b = np.zeros(m, dtype=float)
            
            # Índices para cada tipo de variable
            slack_idx = n
            excess_idx = n + slack_count
            art_idx = n + slack_count + excess_count
            
            # Para rastrear qué variable es básica en cada fila
            basic_var_indices = []
            artificial_indices = []
            
            # Contadores para cada tipo
            s_used = 0
            e_used = 0
            a_used = 0
            
            for i, restriccion in enumerate(restricciones_data):
                coefs = restriccion['coeficientes']
                c_val = float(restriccion['c'])
                signo = restriccion['signo']
                
                print(f"\nProcesando restricción {i+1}: {signo}")
                
                # Variables originales
                for j in range(n):
                    if j < len(coefs):
                        A[i, j] = float(coefs[j])
                    else:
                        A[i, j] = 0.0
                
                # Variables adicionales según el tipo
                if signo == 'leq':
                    # ≤ → Agrega HOLGURA (+1)
                    col_idx = slack_idx + s_used
                    A[i, col_idx] = 1.0
                    basic_var_indices.append(col_idx)  # La holgura es básica
                    s_used += 1
                    print(f"  + Holgura s{s_used} en columna {col_idx}")
                    
                elif signo == 'geq':
                    # ≥ → Agrega EXCESO (-1) y ARTIFICIAL (+1)
                    # Exceso
                    e_col = excess_idx + e_used
                    A[i, e_col] = -1.0
                    e_used += 1
                    
                    # Artificial
                    a_col = art_idx + a_used
                    A[i, a_col] = 1.0
                    artificial_indices.append(a_col)
                    basic_var_indices.append(a_col)  # La artificial es básica
                    a_used += 1
                    print(f"  - Exceso e{e_used} en columna {e_col}")
                    print(f"  + Artificial A{a_used} en columna {a_col}")
                    
                elif signo == 'eq':
                    # = → Solo ARTIFICIAL (+1)
                    a_col = art_idx + a_used
                    A[i, a_col] = 1.0
                    artificial_indices.append(a_col)
                    basic_var_indices.append(a_col)  # La artificial es básica
                    a_used += 1
                    print(f"  + Artificial A{a_used} en columna {a_col}")
                
                b[i] = c_val
            
            # ==============================================
            # 3. NOMBRES DE VARIABLES
            # ==============================================
            var_names = []
            
            # Variables originales
            for j in range(n):
                var_names.append(f"x{j+1}")
            
            # Variables de holgura
            for j in range(slack_count):
                var_names.append(f"s{j+1}")
            
            # Variables de exceso
            for j in range(excess_count):
                var_names.append(f"e{j+1}")
            
            # Variables artificiales
            for j in range(artificial_count):
                var_names.append(f"A{j+1}")
            
            print(f"\nNombres de variables: {var_names}")
            print(f"Índices artificiales: {artificial_indices}")
            
            # ==============================================
            # 4. VECTOR DE COSTOS PARA FASE 2
            # ==============================================
            c_final = np.zeros(total_vars, dtype=float)
            
            # Costos de variables originales
            for j in range(n):
                if j < len(coeficientes):
                    c_final[j] = float(coeficientes[j])
                else:
                    c_final[j] = 0.0
            
            # El resto (holguras, excesos, artificiales) tienen costo 0 en Fase 2
            for j in range(n, total_vars):
                c_final[j] = 0.0
            
            print(f"Vector de costos (Fase 2): {c_final}")
            
            # ==============================================
            # 5. VARIABLES BÁSICAS INICIALES Y COSTOS
            # ==============================================
            basic_vars_init = []
            basic_costs_init = []
            
            for i, basic_idx in enumerate(basic_var_indices):
                if i < len(var_names):
                    var_name = var_names[basic_idx]
                    basic_vars_init.append(var_name)
                    
                    # Determinar costo
                    if var_name.startswith('A'):  # Es artificial
                        # PARA MAXIMIZACIÓN: costo = -1
                        # PARA MINIMIZACIÓN: costo = +1
                        costo = -1.0 if mode == 1 else 1.0
                        basic_costs_init.append(costo)
                        print(f"Variable básica {i+1}: {var_name} (artificial) con costo {costo}")
                    else:  # Holgura (no artificial)
                        basic_costs_init.append(0.0)
                        print(f"Variable básica {i+1}: {var_name} (holgura) con costo 0")
                else:
                    basic_vars_init.append(f"R{i+1}")
                    basic_costs_init.append(0.0)
            
            print(f"Variables básicas iniciales: {basic_vars_init}")
            print(f"Costos básicos iniciales: {basic_costs_init}")
            
            # ==============================================
            # 6. MOSTRAR MATRIZ COMPLETA PARA DEBUG
            # ==============================================
            print(f"\n=== MATRIZ COMPLETA A ===")
            print(f"Forma: {A.shape}")
            for i in range(m):
                row_str = f"R{i+1}: "
                for j in range(total_vars):
                    row_str += f"{A[i,j]:7.2f} "
                row_str += f" = {b[i]:7.2f}"
                print(row_str)
            
            # ==============================================
            # 7. LLAMAR AL MÉTODO DOBLE FASE
            # ==============================================
            print(f"\n=== LLAMANDO two_phase_method_fixed ===")
            solution, Z, all_tables = two_phase_method_fixed(
                A.tolist(), 
                b.tolist(), 
                c_final.tolist(), 
                var_names, 
                basic_vars_init, 
                basic_costs_init, 
                artificial_indices, 
                mode=mode
            )
            
            if solution is None:
                return jsonify({
                    "error": "Problema infactible o no acotado",
                    "tipo": tipo,
                    "estado": "Infactible",
                    "tablas": all_tables if 'all_tables' in locals() else []
                }), 400
            
            # ==============================================
            # 8. FORMATEAR SOLUCIÓN
            # ==============================================
            solucion_formateada = []
            for j in range(n):
                var_name = f"x{j+1}"
                valor = solution.get(var_name, 0.0)
                solucion_formateada.append({
                    "variable": var_name,
                    "valor": float(valor)
                })
            
            # También mostrar valores de holgura/exceso si son diferentes de 0
            for j in range(slack_count):
                var_name = f"s{j+1}"
                valor = solution.get(var_name, 0.0)
                if abs(valor) > 1e-6:
                    solucion_formateada.append({
                        "variable": var_name,
                        "valor": float(valor)
                    })
            
            for j in range(excess_count):
                var_name = f"e{j+1}"
                valor = solution.get(var_name, 0.0)
                if abs(valor) > 1e-6:
                    solucion_formateada.append({
                        "variable": var_name,
                        "valor": float(valor)
                    })
            
            return jsonify({
                "valor_optimo": float(Z),
                "tipo": tipo,
                "estado": "Óptimo encontrado",
                "solucion": solucion_formateada,
                "variables": [solution.get(f"x{j+1}", 0.0) for j in range(n)],
                "tablas": all_tables,
                "problema_info": {
                    "variables_originales": n,
                    "variables_holgura": slack_count,
                    "variables_exceso": excess_count,
                    "variables_artificiales": artificial_count,
                    "total_variables": total_vars,
                    "restricciones": m,
                    "mode": mode
                }
            })
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"ERROR en doblefase: {str(e)}")
            print(f"Detalles: {error_details}")
            
            return jsonify({
                "error": str(e),
                "detalles": error_details,
                "tipo": tipo,
                "estado": "Error en cálculo"
            }), 400
    
    else:
        return jsonify({
            "error": f"Método '{metodo}' no reconocido",
            "tipo": tipo
        }), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render usa PORT
    app.run(host="0.0.0.0", port=port)