import numpy as np
import math

# -------------------------
# Util: eliminar duplicados con tolerancia
# -------------------------
def unique_points(points, tol=1e-7):
    uniques = []
    for x, y in points:
        found = False
        for ux, uy in uniques:
            if abs(x - ux) <= tol and abs(y - uy) <= tol:
                found = True
                break
        if not found:
            uniques.append((x, y))
    return uniques

# ============================
#   FUNCIONES BASE
# ============================
def intersecciones(restricciones):
    puntos = []
    print(f"🔍 Buscando intersecciones entre {len(restricciones)} restricciones")
    
    for i, (a1, b1, c1) in enumerate(restricciones):
        for j, (a2, b2, c2) in enumerate(restricciones):
            if i >= j:
                continue
                
            A = np.array([[a1, b1], [a2, b2]], dtype=float)
            B = np.array([c1, c2], dtype=float)

            if abs(np.linalg.det(A)) < 1e-12:
                continue

            try:
                p = np.linalg.solve(A, B)
                if all(np.isfinite(p)) and p[0] >= -1e-9 and p[1] >= -1e-9:
                    punto = (float(p[0]), float(p[1]))
                    puntos.append(punto)
                    print(f"  ✅ Intersección R{i+1} & R{j+1}: ({punto[0]:.2f}, {punto[1]:.2f})")
            except:
                continue
                
    return puntos

def cortes_con_ejes(restricciones):
    """
    Calcula los cortes (interceptos) de cada restricción con los ejes.
    """
    puntos = []
    print("🔍 Buscando cortes con ejes:")
    
    for i, (a, b, c) in enumerate(restricciones):
        # corte x si a != 0  -> (c/a, 0)
        if abs(a) > 1e-12:
            x = c / a
            if x >= -1e-9:
                punto = (float(x), 0.0)
                puntos.append(punto)
                print(f"  ✅ R{i+1} con eje X: ({punto[0]:.2f}, 0.00)")
        
        # corte y si b != 0  -> (0, c/b)
        if abs(b) > 1e-12:
            y = c / b
            if y >= -1e-9:
                punto = (0.0, float(y))
                puntos.append(punto)
                print(f"  ✅ R{i+1} con eje Y: (0.00, {punto[1]:.2f})")
    return puntos

def filtrar_factibles(puntos, restricciones):
    factibles = []
    print(f"🔍 Filtrando {len(puntos)} puntos por factibilidad")
    
    for x, y in puntos:
        if x < -1e-9 or y < -1e-9:
            continue
            
        ok = True
        for i, (a, b, c) in enumerate(restricciones):
            valor = a * x + b * y
            if valor > c + 1e-9:
                ok = False
                break
                
        if ok:
            factibles.append((round(float(x), 6), round(float(y), 6)))
            print(f"  ✅ Punto factible: ({x:.2f}, {y:.2f})")
        else:
            print(f"  ❌ Punto NO factible: ({x:.2f}, {y:.2f})")
            
    return factibles

# ============================
#   ORDENAR VÉRTICES PARA POLÍGONO
# ============================
def ordenar_vertices_poligono(puntos):
    """
    Ordena los puntos en sentido horario para formar un polígono convexo
    MEJORADO: Maneja mejor los puntos en los ejes para maximización
    """
    if len(puntos) <= 3:
        return puntos
    
    # Para maximización, asegurarnos de incluir el origen y puntos en ejes
    tiene_origen = any(abs(p[0]) < 1e-9 and abs(p[1]) < 1e-9 for p in puntos)
    puntos_en_eje_x = [p for p in puntos if abs(p[1]) < 1e-9 and abs(p[0]) > 1e-9]
    puntos_en_eje_y = [p for p in puntos if abs(p[0]) < 1e-9 and abs(p[1]) > 1e-9]
    
    # Si tenemos puntos en los ejes, usar un método más simple
    if tiene_origen or puntos_en_eje_x or puntos_en_eje_y:
        print("  🔄 Usando ordenamiento especial para puntos en ejes")
        return ordenar_vertices_simple(puntos)
    
    # Método original para otros casos
    punto_inicio = min(puntos, key=lambda p: (p[1], p[0]))
    
    def angulo(p):
        if p == punto_inicio:
            return -float('inf')
        dx = p[0] - punto_inicio[0]
        dy = p[1] - punto_inicio[1]
        return np.arctan2(dy, dx)
    
    puntos_ordenados = sorted(puntos, key=angulo)
    
    hull = []
    for p in puntos_ordenados:
        while len(hull) >= 2:
            a = hull[-2]
            b = hull[-1]
            c = p
            cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if cross > 0:
                break
            hull.pop()
        hull.append(p)
    
    return hull

def ordenar_vertices_simple(puntos):
    """
    Ordenamiento simple pero efectivo para regiones con puntos en ejes
    """
    centro_x = sum(p[0] for p in puntos) / len(puntos)
    centro_y = sum(p[1] for p in puntos) / len(puntos)
    
    def angulo_respecto_centro(p):
        dx = p[0] - centro_x
        dy = p[1] - centro_y
        return np.arctan2(dy, dx)
    
    puntos_ordenados = sorted(puntos, key=angulo_respecto_centro)
    
    inicio = min(puntos_ordenados, key=lambda p: (p[0], p[1]))
    
    if inicio in puntos_ordenados:
        idx = puntos_ordenados.index(inicio)
        puntos_ordenados = puntos_ordenados[idx:] + puntos_ordenados[:idx]
    
    return puntos_ordenados

# ============================
#   FUNCIÓN OBJETIVO
# ============================
def mejor_punto_objetivo(puntos, p, q, tipo="max"):
    mejor = None
    mejor_val = None

    for x, y in puntos:
        z = p * x + q * y
        if mejor_val is None:
            mejor_val = z
            mejor = (x, y)
        else:
            if tipo == "max" and z > mejor_val + 1e-9:
                mejor_val = z
                mejor = (x, y)
            if tipo == "min" and z < mejor_val - 1e-9:
                mejor_val = z
                mejor = (x, y)
                
    print(f"🎯 Punto óptimo: {mejor} con Z = {mejor_val:.2f} ({tipo})")
    return mejor, mejor_val

# ============================
#   DETECCIÓN DE REGIONES NO ACOTADAS
# ============================
def es_region_no_acotada(vertices, restricciones, es_minimizacion):
    """
    Detecta si la región es no acotada en la dirección de optimización
    """
    if len(vertices) < 3:
        return False
    
    tiene_restricciones_ge = any(a > 0 or b > 0 for a, b, c in restricciones)
    
    if es_minimizacion and tiene_restricciones_ge:
        return True
    
    max_x = max(v[0] for v in vertices)
    max_y = max(v[1] for v in vertices)
    
    if max_x > 1000 or max_y > 1000:
        return True
        
    return False

# ============================
#   CALCULAR RANGOS INTELIGENTES
# ============================
def calcular_rangos_inteligentes(vertices, restricciones, es_minimizacion):
    if not vertices:
        return (0.0, 100.0), (0.0, 100.0)
    
    xs = [v[0] for v in vertices]
    ys = [v[1] for v in vertices]
    
    x_max = max(xs) if xs else 10
    y_max = max(ys) if ys else 10
    
    print(f"🔍 Valores máximos encontrados: x={x_max}, y={y_max}")
    
    if x_max <= 20 and y_max <= 20:
        margen_x = max(x_max * 0.4, 3)
        margen_y = max(y_max * 0.4, 3)
        x_range = (0.0, float(x_max + margen_x))
        y_range = (0.0, float(y_max + margen_y))
        print("📏 Usando escala PEQUEÑA")
        
    elif x_max <= 100 and y_max <= 100:
        margen_x = max(x_max * 0.2, 10)
        margen_y = max(y_max * 0.2, 10)
        x_range = (0.0, float(x_max + margen_x))
        y_range = (0.0, float(y_max + margen_y))
        print("📏 Usando escala MEDIANA")
        
    else:
        margen_x = max(x_max * 0.15, 50)
        margen_y = max(y_max * 0.15, 50)
        x_range = (0.0, float(x_max + margen_x))
        y_range = (0.0, float(y_max + margen_y))
        print("📏 Usando escala GRANDE")
    
    def redondear_bonito(valor):
        if valor <= 20:
            return math.ceil(valor)
        elif valor <= 100:
            return math.ceil(valor / 10) * 10
        else:
            return math.ceil(valor / 50) * 50
    
    x_range = (0.0, float(redondear_bonito(x_range[1])))
    y_range = (0.0, float(redondear_bonito(y_range[1])))
    
    print(f"📐 Rangos finales: X{x_range}, Y{y_range}")
    return x_range, y_range

# ============================
#   ENCONTRAR TODOS LOS VÉRTICES
# ============================
def encontrar_vertices_completos(restricciones, es_minimizacion=False):
    print(f"\n🔍 INICIANDO BÚSQUEDA DE VÉRTICES (Minimización: {es_minimizacion})")
    print(f"Restricciones: {restricciones}")
    
    vertices = []
    
    # 1) Intersecciones entre todas las combinaciones de restricciones
    for i in range(len(restricciones)):
        for j in range(i + 1, len(restricciones)):
            a1, b1, c1 = restricciones[i]
            a2, b2, c2 = restricciones[j]
            
            A = np.array([[a1, b1], [a2, b2]], dtype=float)
            B = np.array([c1, c2], dtype=float)
            
            if abs(np.linalg.det(A)) > 1e-12:
                try:
                    p = np.linalg.solve(A, B)
                    if p[0] >= -1e-9 and p[1] >= -1e-9:
                        punto = (float(p[0]), float(p[1]))
                        factible = True
                        for a, b, c in restricciones:
                            if a * p[0] + b * p[1] > c + 1e-9:
                                factible = False
                                break
                        if factible:
                            vertices.append(punto)
                            print(f"  ✅ Intersección R{i+1} & R{j+1}: ({punto[0]:.2f}, {punto[1]:.2f})")
                except:
                    continue
    
    # 2) Cortes con ejes
    for i, (a, b, c) in enumerate(restricciones):
        if abs(a) > 1e-12:
            x = c / a
            if x >= -1e-9:
                punto = (float(x), 0.0)
                if all(a * punto[0] + b * punto[1] <= c + 1e-9 for a, b, c in restricciones):
                    vertices.append(punto)
                    print(f"  ✅ R{i+1} con eje X: ({punto[0]:.2f}, 0.00)")
        
        if abs(b) > 1e-12:
            y = c / b
            if y >= -1e-9:
                punto = (0.0, float(y))
                if all(a * punto[0] + b * punto[1] <= c + 1e-9 for a, b, c in restricciones):
                    vertices.append(punto)
                    print(f"  ✅ R{i+1} con eje Y: (0.00, {punto[1]:.2f})")
    
    # 3) Origen SOLO para maximización
    if not es_minimizacion:
        if all(a * 0.0 + b * 0.0 <= c + 1e-9 for a, b, c in restricciones):
            vertices.append((0.0, 0.0))
            print("  ✅ Origen (0,0) agregado (maximización)")
    
    # 4) Eliminar duplicados
    vertices = unique_points(vertices, tol=1e-7)
    
    print(f"📊 Total de vértices encontrados: {len(vertices)}")
    for v in vertices:
        print(f"  • ({v[0]:.2f}, {v[1]:.2f})")
    
    return vertices

# ============================
#   FUNCIÓN PRINCIPAL
# ============================
def calcular_region_factible(restricciones, funcion_objetivo):
    """
    restricciones: lista de tuplas (a,b,c) que representan a*x + b*y <= c
    funcion_objetivo: (p, q, 'max'|'min')
    """
    p, q, tipo = funcion_objetivo
    es_minimizacion = (tipo == "min")
    
    print(f"\n" + "="*50)
    print(f"🚀 INICIANDO CÁLCULO - {tipo.upper()} Z = {p}x + {q}y")
    print(f"Restricciones: {restricciones}")
    print("="*50)

    # 1) Encontrar todos los vértices
    vertices = encontrar_vertices_completos(restricciones, es_minimizacion)
    
    print("\n🔍 VÉRTICES FINALES ANTES DE ORDENAR:")
    for i, v in enumerate(vertices):
        print(f"  {i+1}. ({v[0]:.2f}, {v[1]:.2f})")
    
    if not vertices:
        print("❌ REGIÓN VACÍA - No se encontraron vértices factibles")
        return {
            "vertices_factibles": [],
            "punto_optimo": None,
            "valor_optimo": None,
            "rango_x": (0.0, 10.0),
            "rango_y": (0.0, 10.0),
            "funcion_objetivo": {"p": p, "q": q, "tipo": tipo},
            "restricciones": restricciones,
            "problema": "region vacia"
        }

    # 4) Ordenar vértices para el polígono
    vertices_ordenados = ordenar_vertices_poligono(vertices)
    
    print(f"\n📋 VÉRTICES ORDENADOS PARA POLÍGONO:")
    for i, v in enumerate(vertices_ordenados):
        print(f"  {i+1}. ({v[0]:.2f}, {v[1]:.2f})")

    # 5) Encontrar punto óptimo
    punto_opt, valor_opt = mejor_punto_objetivo(vertices, p, q, tipo)

    # 6) Calcular rangos inteligentes
    rx, ry = calcular_rangos_inteligentes(vertices, restricciones, es_minimizacion)

    # 7) Información adicional para el frontend
    region_no_acotada = es_region_no_acotada(vertices, restricciones, es_minimizacion)
    
    print(f"📐 RANGOS FINALES: X{rx}, Y{ry}")
    print(f"🔍 Región no acotada: {region_no_acotada}")
    print("✅ CÁLCULO COMPLETADO\n")

    return {
        "vertices_factibles": vertices_ordenados,
        "punto_optimo": punto_opt,
        "valor_optimo": valor_opt,
        "rango_x": rx,
        "rango_y": ry,
        "funcion_objetivo": {"p": p, "q": q, "tipo": tipo},
        "restricciones": restricciones,
        "region_no_acotada": region_no_acotada
    }
