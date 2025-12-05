// Colores para la visualización
const colores = {
    region: 'rgba(128, 128, 128, 0.3)',
    borde: 'rgba(0, 100, 255, 0.8)',
    puntos: 'rgba(0, 100, 255, 0.8)',
    optimo: 'rgba(255, 0, 0, 1)',
    lineas: 'rgba(9, 166, 163, 0.6)',
    ejes: 'rgba(0, 0, 0, 0.3)'
};

let chart = null;
let contadorRestricciones = 1;
let contadorVariables = 2; // Empezamos con 2 variables
let metodoSeleccionado = 'grafico'; // Método por defecto
let regionData = null;

// PLUGIN PERSONALIZADO para dibujar la región factible
const regionFactiblePlugin = {
    id: 'regionFactible',
    beforeDraw(chart) {
        if (!regionData || regionData.vertices.length < 3) return;
        
        const ctx = chart.ctx;
        const xAxis = chart.scales.x;
        const yAxis = chart.scales.y;
        
        // Convertir coordenadas de datos a píxeles para TODOS los vértices
        const puntosPixel = regionData.vertices.map(vertice => ({
            x: xAxis.getPixelForValue(vertice[0]),
            y: yAxis.getPixelForValue(vertice[1])
        }));
        
        // Dibujar la región factible
        ctx.save();
        ctx.beginPath();
        
        // Mover al primer punto
        ctx.moveTo(puntosPixel[0].x, puntosPixel[0].y);
        
        // Dibujar líneas hacia los demás puntos
        for (let i = 1; i < puntosPixel.length; i++) {
            ctx.lineTo(puntosPixel[i].x, puntosPixel[i].y);
        }
        
        // Cerrar el polígono
        ctx.closePath();
        
        // Rellenar la región con color GRIS
        ctx.fillStyle = colores.region;
        ctx.fill();
        
        // Dibujar borde AZUL
        ctx.strokeStyle = colores.borde;
        ctx.lineWidth = 2.5;
        ctx.stroke();
        
        ctx.restore();
    }
};

// Registrar el plugin
Chart.register(regionFactiblePlugin);

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    console.log('🔧 Programación Lineal - Listo!');
    inicializarFormulario();
    actualizarBotonesMetodo();
    actualizarRestriccionesVariables();
    actualizarBotonResolver(); // Nueva función
});

// Inicializar formulario
function inicializarFormulario() {
    // Configurar eventos para los botones de método
    document.getElementById('btnGrafico').addEventListener('click', () => {
        seleccionarMetodo('grafico');
    });
    
    document.getElementById('btnDobleFase').addEventListener('click', () => {
        seleccionarMetodo('doblefase');
    });
    
    // Configurar el formulario
    document.getElementById('problemaForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        // Verificar si el botón está deshabilitado
        const btnResolver = document.getElementById('btnResolver');
        if (btnResolver.disabled) {
            alert('⚠️ El método gráfico solo funciona con 2 variables. Selecciona "Doble Fase" o reduce el número de variables.');
            return;
        }
        await resolverProblema();
    });
}

// Seleccionar método
function seleccionarMetodo(metodo) {
    metodoSeleccionado = metodo;
    actualizarBotonesMetodo();
    actualizarBotonResolver(); // Actualizar estado del botón resolver
    
    // Mostrar/ocultar secciones según el método
    const chartContainer = document.getElementById('chartContainer');
    const tablaResultados = document.getElementById('tablaResultados');
    
    if (metodo === 'grafico') {
        chartContainer.style.display = 'block';
        tablaResultados.style.display = 'none';
        document.getElementById('infoText').textContent = 
            'Método gráfico: Visualización 2D de la región factible (máx. 2 variables)';
        
        // Actualizar mensaje si hay más de 2 variables
        if (contadorVariables > 2) {
            document.getElementById('infoText').textContent = 
                '⚠️ El método gráfico requiere máximo 2 variables. Selecciona "Doble Fase" o reduce variables.';
        }
    } else {
        chartContainer.style.display = 'none';
        tablaResultados.style.display = 'block';
        document.getElementById('infoText').textContent = 
            'Método Doble Fase: Resolución de problemas con variables de holgura y artificiales';
    }
}

// Actualizar estado de los botones de método
function actualizarBotonesMetodo() {
    const btnGrafico = document.getElementById('btnGrafico');
    const btnDobleFase = document.getElementById('btnDobleFase');
    
    // Resetear ambos botones
    btnGrafico.classList.remove('active');
    btnDobleFase.classList.remove('active');
    
    // Activar el botón seleccionado
    if (metodoSeleccionado === 'grafico') {
        btnGrafico.classList.add('active');
        // NO deshabilitamos el botón gráfico, solo mostramos el mensaje
        btnGrafico.disabled = false;
        btnGrafico.title = '';
    } else {
        btnDobleFase.classList.add('active');
        btnGrafico.disabled = false;
        btnGrafico.title = '';
    }
}

// NUEVA FUNCIÓN: Actualizar estado del botón "Resolver Problema"
function actualizarBotonResolver() {
    const btnResolver = document.getElementById('btnResolver');
    
    // Verificar si el método gráfico está seleccionado y hay más de 2 variables
    if (metodoSeleccionado === 'grafico' && contadorVariables > 2) {
        btnResolver.disabled = true;
        btnResolver.title = 'El método gráfico solo funciona con 2 variables. Selecciona "Doble Fase" o reduce variables.';
        btnResolver.style.opacity = '0.6';
        btnResolver.style.cursor = 'not-allowed';
        btnResolver.innerHTML = '🚫 Método Gráfico requiere 2 variables';
    } else {
        btnResolver.disabled = false;
        btnResolver.title = '';
        btnResolver.style.opacity = '1';
        btnResolver.style.cursor = 'pointer';
        btnResolver.innerHTML = '🚀 Resolver Problema';
    }
}

// Agregar variable a la función objetivo
function agregarVariable() {
    contadorVariables++;
    const variablesContainer = document.getElementById('variables-container');
    
    const variableItem = document.createElement('div');
    variableItem.className = 'variable-item';
    variableItem.innerHTML = `
        <span class="variable-plus">+</span>
        <input type="number" step="any" name="coef_${contadorVariables-1}" value="0" required>
        <span class="variable-name">x${contadorVariables}</span>
    `;
    
    variablesContainer.appendChild(variableItem);
    
    // Actualizar restricciones para incluir la nueva variable
    actualizarRestriccionesVariables();
    
    // Si estamos en método gráfico y ahora tenemos más de 2 variables
    if (metodoSeleccionado === 'grafico' && contadorVariables > 2) {
        // Cambiar automáticamente a Doble Fase
        seleccionarMetodo('doblefase');
    }
    
    actualizarBotonesMetodo();
    actualizarBotonResolver(); // Actualizar botón resolver
}

// Quitar variable de la función objetivo
function quitarVariable() {
    if (contadorVariables > 2) {
        contadorVariables--;
        const variablesContainer = document.getElementById('variables-container');
        const variableItems = variablesContainer.querySelectorAll('.variable-item');
        
        if (variableItems.length > 0) {
            variablesContainer.removeChild(variableItems[variableItems.length - 1]);
        }
        
        // Actualizar restricciones
        actualizarRestriccionesVariables();
        actualizarBotonesMetodo();
        actualizarBotonResolver(); // Actualizar botón resolver
    } else {
        alert('Debe haber al menos 2 variables');
    }
}

// Actualizar inputs de restricciones según número de variables
function actualizarRestriccionesVariables() {
    const restricciones = document.querySelectorAll('.restriccion-item');
    
    restricciones.forEach((restriccion, index) => {
        const id = restriccion.getAttribute('data-id');
        const inputsContainer = restriccion.querySelector('.restriccion-inputs');
        
        // Limpiar container
        inputsContainer.innerHTML = '';
        
        // Agregar inputs para cada variable
        for (let i = 0; i < contadorVariables; i++) {
            const variableDiv = document.createElement('div');
            variableDiv.className = 'variable-coef';
            
            variableDiv.innerHTML = `
                <input type="number" step="any" name="a_${id}_${i}" value="${i < 2 ? (i === 0 ? 1 : 0) : 0}" required>
                <span class="variable-coef-name">x${i+1}</span>
                ${i < contadorVariables - 1 ? '<span class="variable-coef-plus">+</span>' : ''}
            `;
            
            inputsContainer.appendChild(variableDiv);
        }
        
        // Agregar selector de desigualdad y término independiente
        const signoDiv = document.createElement('div');
        signoDiv.className = 'restriccion-signo';
        signoDiv.innerHTML = `
            <select name="signo_${id}">
                <option value="leq">≤</option>
                <option value="geq">≥</option>
                <option value="eq">=</option>
            </select>
            <input type="number" step="any" name="c_${id}" value="100" required>
        `;
        
        inputsContainer.appendChild(signoDiv);
    });
}

// Funciones para manejar restricciones dinámicas
function añadirRestriccion() {
    contadorRestricciones++;
    const restriccionesContainer = document.getElementById('restricciones-container');
    
    const nuevaRestriccion = document.createElement('div');
    nuevaRestriccion.className = 'restriccion-item';
    nuevaRestriccion.setAttribute('data-id', contadorRestricciones);
    
    nuevaRestriccion.innerHTML = `
        <div class="restriccion-header">
            <span class="restriccion-title">📐 Restricción ${contadorRestricciones}</span>
            <button type="button" class="btn-eliminar" onclick="eliminarRestriccion(${contadorRestricciones})">🗑️ Eliminar</button>
        </div>
        <div class="restriccion-inputs" id="restriccion-inputs-${contadorRestricciones}">
            <!-- Los inputs se generarán dinámicamente -->
        </div>
    `;
    
    restriccionesContainer.appendChild(nuevaRestriccion);
    actualizarRestriccionesVariables();
}

function eliminarRestriccion(id) {
    if (contadorRestricciones > 1) {
        const restriccion = document.querySelector(`[data-id="${id}"]`);
        if (restriccion) {
            restriccion.remove();
            const restriccionesRestantes = document.querySelectorAll('.restriccion-item');
            contadorRestricciones = restriccionesRestantes.length;
            
            // Renumerar las restricciones restantes
            restriccionesRestantes.forEach((restriccion, index) => {
                const nuevoId = index + 1;
                restriccion.setAttribute('data-id', nuevoId);
                restriccion.querySelector('.restriccion-title').textContent = `📐 Restricción ${nuevoId}`;
                restriccion.querySelector('.btn-eliminar').setAttribute('onclick', `eliminarRestriccion(${nuevoId})`);
            });
        }
    } else {
        alert('Debe haber al menos una restricción');
    }
}

// Resolver problema según método seleccionado
async function resolverProblema() {
    // Verificación adicional por si acaso
    if (metodoSeleccionado === 'grafico' && contadorVariables > 2) {
        alert('⚠️ El método gráfico solo funciona con 2 variables. Selecciona "Doble Fase" o reduce el número de variables.');
        return;
    }
    
    const loading = document.getElementById('loading');
    const loadingText = document.getElementById('loadingText');
    
    loading.style.display = 'block';
    loadingText.textContent = metodoSeleccionado === 'grafico' 
        ? 'Calculando región factible...' 
        : 'Aplicando método Doble Fase...';

    const formData = new FormData(document.getElementById('problemaForm'));
    
    // Obtener coeficientes de la función objetivo
    const coeficientes = [];
    for (let i = 0; i < contadorVariables; i++) {
        coeficientes.push(parseFloat(formData.get(`coef_${i}`)) || 0);
    }
    
    const tipo = formData.get('tipo');
    
    // Obtener restricciones
    const restricciones = [];
    const elementosRestricciones = document.querySelectorAll('.restriccion-item');
    
    elementosRestricciones.forEach((elemento) => {
        const id = elemento.getAttribute('data-id');
        const coeficientesRestriccion = [];
        
        // Obtener coeficientes de la restricción
        for (let i = 0; i < contadorVariables; i++) {
            const valor = parseFloat(formData.get(`a_${id}_${i}`)) || 0;
            coeficientesRestriccion.push(valor);
        }
        
        const signo = formData.get(`signo_${id}`);
        const c = parseFloat(formData.get(`c_${id}`)) || 0;
        
        restricciones.push({
            coeficientes: coeficientesRestriccion,
            signo: signo,
            c: c
        });
    });

    // Preparar datos para enviar a Flask
    const payload = {
        metodo: metodoSeleccionado,
        variables: contadorVariables,
        coeficientes: coeficientes,
        tipo: tipo,
        restricciones: restricciones
    };

    console.log("Payload a enviar:", payload);

    try {
        // Enviar los datos a Flask usando fetch
        const resp = await fetch('/resolver', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        if (!resp.ok) {
            throw new Error(`Error del servidor: ${resp.status}`);
        }

        const data = await resp.json();
        
        // Mostrar resultados según el método
        if (metodoSeleccionado === 'grafico') {
            visualizarResultadosGrafico(data);
        } else {
            mostrarResultadosDobleFase(data);
        }

    } catch (error) {
        alert('❌ Error: ' + error.message);
        console.error('Error:', error);
    } finally {
        loading.style.display = 'none';
    }
}

// Función para generar puntos para las líneas de restricción
function generarLineaRestriccionCompleta(a, b, c, xRange, yRange, signoOriginal) {
    const puntos = [];
    
    // Para regiones no acotadas, extender más las líneas
    const xMax = xRange[1];
    const yMax = yRange[1];
    
    if (Math.abs(b) > 1e-12 && Math.abs(a) > 1e-12) {
        // Recta inclinada: y = (c - a*x)/b
        
        // Calcular puntos en los extremos del rango visible
        const intersecciones = [];
        
        // Intersección con borde izquierdo (x = 0)
        const yLeft = c / b;
        if (yLeft >= -1e-9 && yLeft <= yMax) {
            intersecciones.push({x: 0, y: yLeft});
        }
        
        // Intersección con borde derecho (x = xMax)
        const yRight = (c - a * xMax) / b;
        if (yRight >= -1e-9 && yRight <= yMax) {
            intersecciones.push({x: xMax, y: yRight});
        }
        
        // Intersección con borde inferior (y = 0)
        const xBottom = c / a;
        if (xBottom >= -1e-9 && xBottom <= xMax) {
            intersecciones.push({x: xBottom, y: 0});
        }
        
        // Intersección con borde superior (y = yMax)
        const xTop = (c - b * yMax) / a;
        if (xTop >= -1e-9 && xTop <= xMax) {
            intersecciones.push({x: xTop, y: yMax});
        }
        
        // Eliminar duplicados
        const puntosUnicos = [];
        intersecciones.forEach(p => {
            if (!puntosUnicos.some(existing => 
                Math.abs(existing.x - p.x) < 1e-9 && Math.abs(existing.y - p.y) < 1e-9
            )) {
                puntosUnicos.push(p);
            }
        });
        
        // Ordenar por x
        puntos.push(...puntosUnicos.sort((a, b) => a.x - b.x));
        
    } else if (Math.abs(b) < 1e-12 && Math.abs(a) > 1e-12) {
        // Línea vertical: x = c/a
        const x = c / a;
        if (x >= -1e-9 && x <= xMax) {
            puntos.push({x: x, y: 0});
            puntos.push({x: x, y: yMax});
        }
    } else if (Math.abs(a) < 1e-12 && Math.abs(b) > 1e-12) {
        // Línea horizontal: y = c/b
        const y = c / b;
        if (y >= -1e-9 && y <= yMax) {
            puntos.push({x: 0, y: y});
            puntos.push({x: xMax, y: y});
        }
    }
    
    return puntos;
}

// Función para ordenar vértices en sentido horario
function ordenarVerticesPoligono(vertices) {
    if (vertices.length < 3) return vertices;
    
    const centroX = vertices.reduce((sum, v) => sum + v[0], 0) / vertices.length;
    const centroY = vertices.reduce((sum, v) => sum + v[1], 0) / vertices.length;
    
    return vertices.sort((a, b) => {
        const anguloA = Math.atan2(a[1] - centroY, a[0] - centroX);
        const anguloB = Math.atan2(b[1] - centroY, b[0] - centroX);
        return anguloA - anguloB;
    });
}

// Función para visualizar resultados gráficos
function visualizarResultadosGrafico(data) {
    const ctx = document.getElementById('graficoMetodo').getContext('2d');

    console.log("Datos para gráfico:", data);

    if (chart) chart.destroy();

    const datasets = [];
    const vet = data.vertices_factibles || [];
    const esNoAcotada = data.region_no_acotada || false;

    // --- ALMACENAR DATOS DE LA REGIÓN PARA EL PLUGIN ---
    if (vet.length >= 3) {
        const verticesOrdenados = ordenarVerticesPoligono(vet);
        regionData = {
            vertices: verticesOrdenados,
            color: colores.region,
            borderColor: colores.borde,
            borderWidth: 2.5
        };
    } else {
        regionData = null;
    }

    // --- 1) LÍNEAS DE RESTRICCIÓN ---
    (data.restricciones || []).forEach((restriccion, index) => {
        // Solo mostrar líneas si hay 2 variables
        if (contadorVariables === 2) {
            const a = restriccion[0], b = restriccion[1], c = restriccion[2];
            const lineaPuntos = generarLineaRestriccionCompleta(a, b, c, data.rango_x, data.rango_y);

            if (lineaPuntos.length >= 2) {
                // Determinar el signo basado en si la restricción fue convertida
                const esConversion = a < 0 || b < 0 || c < 0;
                const signo = esConversion ? "≥" : "≤";
                
                // Mostrar los valores originales (sin el signo negativo de la conversión)
                const aMostrar = esConversion ? -a : a;
                const bMostrar = esConversion ? -b : b;
                const cMostrar = esConversion ? -c : c;
                
                datasets.push({
                    label: `📐 ${aMostrar}x + ${bMostrar}y ${signo} ${cMostrar}`,
                    data: lineaPuntos,
                    borderColor: `hsl(${index * 60}, 70%, 50%)`,
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false,
                    tension: 0,
                    showLine: true,
                    type: 'line',
                    order: 1
                });
            }
        }
    });

    // --- 2) Vértices factibles ---
    if (vet.length > 0 && contadorVariables === 2) {
        datasets.push({
            label: '🔵 Vértices',
            data: vet.map(p => ({ x: p[0], y: p[1] })),
            backgroundColor: colores.puntos,
            borderColor: '#ffffff',
            borderWidth: 2,
            pointRadius: 6,
            showLine: false,
            type: 'scatter',
            order: 2
        });
    }

    // --- 3) Punto óptimo ---
    if (data.punto_optimo && contadorVariables === 2) {
        datasets.push({
            label: '🎯 Óptimo',
            data: [{ x: data.punto_optimo[0], y: data.punto_optimo[1] }],
            backgroundColor: colores.optimo,
            borderColor: '#ffffff',
            borderWidth: 3,
            pointRadius: 10,
            showLine: false,
            type: 'scatter',
            order: 3
        });
    }

    // Crear el gráfico solo si hay 2 variables
    if (contadorVariables === 2) {
        chart = new Chart(ctx, {
            type: 'scatter',
            data: { datasets: datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        min: data.rango_x ? data.rango_x[0] : 0,
                        max: data.rango_x ? data.rango_x[1] : 100,
                        ticks: { 
                            stepSize: data.rango_x ? Math.max(10, Math.ceil(data.rango_x[1] / 10)) : 10
                        },
                        title: {
                            display: true,
                            text: 'x₁'
                        }
                    },
                    y: {
                        type: 'linear',
                        min: data.rango_y ? data.rango_y[0] : 0,
                        max: data.rango_y ? data.rango_y[1] : 100,
                        ticks: { 
                            stepSize: data.rango_y ? Math.max(10, Math.ceil(data.rango_y[1] / 10)) : 10
                        },
                        title: {
                            display: true,
                            text: 'x₂'
                        }
                    }
                },
                plugins: {
                    legend: { 
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const p = context.raw;
                                return `(${p.x.toFixed(1)}, ${p.y.toFixed(1)})`;
                            }
                        }
                    }
                },
                elements: { 
                    line: { 
                        tension: 0
                    }
                }
            }
        });
    } else {
        // Si no hay 2 variables, ocultar el gráfico
        const chartContainer = document.getElementById('chartContainer');
        chartContainer.style.display = 'none';
    }

    // Actualizar resultados textuales
    let infoProblema = '';
    if (esNoAcotada) {
        infoProblema = '<br><strong>⚠️ Región No Acotada</strong>';
    }

    if (contadorVariables === 2) {
        document.getElementById('puntosResultados').innerHTML = `
            <strong>📊 Vértices Factibles (${vet.length}):</strong><br>
            ${vet.map(p => `(${p[0].toFixed(1)}, ${p[1].toFixed(1)})`).join('<br>')}
            ${infoProblema}
        `;
    } else {
        document.getElementById('puntosResultados').innerHTML = `
            <strong>📊 Solución en ${contadorVariables} dimensiones:</strong><br>
            ${data.solucion ? data.solucion.map(v => `${v.variable} = ${v.valor.toFixed(2)}`).join('<br>') : 'No disponible'}
        `;
    }

    if (data.punto_optimo && contadorVariables === 2) {
        document.getElementById('solucionResultados').innerHTML = `
            <strong>🎯 Solución Óptima:</strong><br>
            Punto: (${data.punto_optimo[0].toFixed(1)}, ${data.punto_optimo[1].toFixed(1)})<br>
            Valor Z: ${data.valor_optimo.toFixed(2)}<br>
            Tipo: ${data.tipo === 'max' ? 'Maximización' : 'Minimización'}
        `;
    } else if (data.valor_optimo) {
        document.getElementById('solucionResultados').innerHTML = `
            <strong>🎯 Solución Óptima:</strong><br>
            Valor Z: ${data.valor_optimo.toFixed(2)}<br>
            Tipo: ${data.tipo === 'max' ? 'Maximización' : 'Minimización'}
        `;
    } else {
        document.getElementById('solucionResultados').innerHTML = `
            <strong>❌ No se encontró solución óptima</strong><br>
            ${data.problema || 'La región factible podría estar vacía'}
        `;
    }
}

// Función para mostrar resultados del método Doble Fase
function mostrarResultadosDobleFase(data) {
    const tablaResultados = document.getElementById('tablaResultados');
    
    // Mostrar información básica
    document.getElementById('solucionResultados').innerHTML = `
        <strong>🎯 Solución Óptima:</strong><br>
        Valor Z: ${data.valor_optimo ? data.valor_optimo.toFixed(2) : 'N/A'}<br>
        Tipo: ${data.tipo === 'max' ? 'Maximización' : 'Minimización'}<br>
        Estado: ${data.estado || 'Completado'}
    `;
    
    // Mostrar información del problema
    if (data.problema_info) {
        document.getElementById('puntosResultados').innerHTML = `
            <strong>📊 Información del Problema:</strong><br>
            Variables originales: ${data.problema_info.variables_originales}<br>
            Variables de holgura: ${data.problema_info.variables_holgura}<br>
            Variables de exceso: ${data.problema_info.variables_exceso}<br>
            Variables artificiales: ${data.problema_info.variables_artificiales}<br>
            Total variables: ${data.problema_info.total_variables}<br>
            Restricciones: ${data.problema_info.restricciones}
        `;
    }
    
    // Mostrar valores de variables
    if (data.solucion) {
        let solucionHTML = '<strong>🔢 Solución Óptima:</strong><br>';
        data.solucion.forEach(variable => {
            solucionHTML += `${variable.variable} = ${variable.valor.toFixed(4)}<br>`;
        });
        solucionHTML += `<br><strong>Valor Z = ${data.valor_optimo.toFixed(4)}</strong>`;
        document.getElementById('puntosResultados').innerHTML += '<br>' + solucionHTML;
    }
    
    // Mostrar tablas simplex si están disponibles
    if (data.tablas && data.tablas.length > 0) {
        let tablaHTML = '<strong>📊 PROCESO DEL MÉTODO DOBLE FASE:</strong><br>';
        
        // Agrupar tablas por fase
        const fases = {
            1: [],
            1.5: [],
            2: []
        };
        
        data.tablas.forEach((tabla, index) => {
            fases[tabla.phase] = fases[tabla.phase] || [];
            fases[tabla.phase].push({...tabla, index});
        });
        
        // Mostrar Fase 1
        if (fases[1].length > 0) {
            tablaHTML += '<h3>📋 FASE 1: Minimización de Variables Artificiales</h3>';
            fases[1].forEach(tabla => {
                tablaHTML += crearTablaHTML(tabla);
            });
        }
        
        // Mostrar eliminación de artificiales (si existe)
        if (fases[1.5] && fases[1.5].length > 0) {
            tablaHTML += '<h3>🔄 Eliminación de Variables Artificiales Básicas</h3>';
            fases[1.5].forEach(tabla => {
                tablaHTML += crearTablaHTML(tabla);
            });
        }
        
        // Mostrar Fase 2
        if (fases[2].length > 0) {
            tablaHTML += '<h3>📋 FASE 2: Optimización de la Función Original</h3>';
            fases[2].forEach(tabla => {
                tablaHTML += crearTablaHTML(tabla);
            });
        }
        
        tablaResultados.innerHTML = tablaHTML;
        tablaResultados.style.display = 'block';
    } else {
        tablaResultados.innerHTML = '<strong>📊 Método Doble Fase:</strong><br>No se generaron tablas del proceso.';
        tablaResultados.style.display = 'block';
    }
}

// Función para crear HTML de una tabla simplex
function crearTablaHTML(tabla) {
    let html = `<div class="tableau-container">
        <h4>${tabla.title || `Iteración ${tabla.iteration}`}</h4>`;
    
    if (tabla.pivot_info) {
        html += `<div class="pivot-info">
            <strong>Pivote:</strong> Entra ${tabla.pivot_info.entra}, Sale ${tabla.pivot_info.sale}
        </div>`;
    }
    
    html += `<div class="table-scroll">
        <table class="simplex-table">`;
    
    // Encabezados
    html += '<tr>';
    tabla.headers.forEach(header => {
        html += `<th>${header}</th>`;
    });
    html += '</tr>';
    
    // Datos
    tabla.data.forEach((fila, filaIndex) => {
        const esFilaZjCj = fila[0] === 'Zj-Cj';
        html += '<tr>';
        
        fila.forEach((celda, colIndex) => {
            let clase = '';
            let contenido = celda;
            
            // Formatear números
            if (typeof celda === 'number') {
                contenido = Math.abs(celda) < 0.0001 ? '0' : celda.toFixed(4);
                
                // Resaltar valores importantes
                if (Math.abs(celda) < 0.0001 && celda !== 0) {
                    contenido = '~0';
                }
            }
            
            // Estilos especiales
            if (esFilaZjCj) {
                clase = 'zj-cj-row';
                // Resaltar valores positivos/negativos según optimización
                if (typeof celda === 'number' && colIndex > 0 && colIndex < fila.length - 1) {
                    if (celda > 0.0001) clase += ' positive';
                    else if (celda < -0.0001) clase += ' negative';
                }
            }
            
            // Resaltar celda pivote
            if (tabla.pivot_info && 
                !esFilaZjCj && 
                filaIndex === tabla.pivot_info.row && 
                colIndex === tabla.pivot_info.col + 1) {
                clase += ' pivot-cell';
            }
            
            // Primera columna (nombres de variables)
            if (colIndex === 0) {
                clase += ' variable-cell';
            }
            
            // Última columna (LD)
            if (colIndex === fila.length - 1) {
                clase += ' ld-cell';
            }
            
            html += `<td class="${clase}">${contenido}</td>`;
        });
        
        html += '</tr>';
    });
    
    html += '</table></div>';
    
    // Información adicional
    if (tabla.W_value !== undefined) {
        html += `<div class="table-info">
            <strong>W = ${tabla.W_value.toFixed(6)}</strong> (suma de variables artificiales)
        </div>`;
    }
    
    if (tabla.Z_value !== undefined) {
        html += `<div class="table-info">
            <strong>Z = ${tabla.Z_value.toFixed(4)}</strong> (valor óptimo)
        </div>`;
    }
    
    html += '</div><br>';
    return html;
}

// Exportar funciones para uso en HTML
window.agregarVariable = agregarVariable;
window.quitarVariable = quitarVariable;
window.añadirRestriccion = añadirRestriccion;
window.eliminarRestriccion = eliminarRestriccion;
window.seleccionarMetodo = seleccionarMetodo;