## Estrategias de Entrenamiento y Optimización ante Desequilibrio de Clases

La prevalencia de código vulnerable en un software real es baja; en bases de datos representativas del mundo real, las muestras que presentan debilidades o fallos de seguridad representan típicamente entre el 1% y el 5.4% del volumen total de funciones^^. Entrenar un modelo de aprendizaje profundo bajo estas condiciones empleando la pérdida de entropía cruzada binaria (BCE) estándar provoca que el optimizador se sesgue de manera severa hacia la clase mayoritaria (benigna) para maximizar la métrica de exactitud global, derivando en un modelo incapaz de recuperar las vulnerabilidades críticas del sistema^^.

### Reformulaciones de la Función de Pérdida

Para revertir el sesgo del desequilibrio de clases, es necesario sustituir o com

plementar el cálculo del gradiente en el optimizador por enfoques sensibles a la frecuencia y a la dificultad de aprendizaje de los datos:

* **Weighted Cross-Entropy (WCE)** : Modifica la entropía cruzada estándar asignando pesos fijos y diferenciados a cada una de las clases representadas en el lote, penalizando de forma más severa los errores cometidos en el procesamiento de muestras de la clase minoritaria (vulnerable)^^:

$$
\mathcal{L}_{\text{WCE}} = - \frac{1}{N} \sum_{i=1}^{N} \left[ w_1 y_i \log(\hat{y}_i) + w_0 (1 - y_i) \log(1 - \hat{y}_i) \right]
$$

Donde **$y_i$** es la etiqueta real de la muestra, **$\hat{y}_i$** la predicción probabilística estimada por la sigmoide, y **$w_1, w_0$** los coeficientes de escala^^. Si se asigna **$w_1 > w_0$** de acuerdo con la inversa de la proporción de clases, se incrementa notablemente la sensibilidad de recuperación ( *recall* ) de vulnerabilidades raras^^.

* **Focal Loss (Pérdida Focalizada)** : Propuesta originalmente por Lin et al., extiende el concepto de entropía cruzada al incorporar un factor de modulación que reduce la influencia de los ejemplos benignos fáciles de clasificar durante el descenso de gradiente^^. Esto fuerza al modelo a concentrar su presupuesto de aprendizaje en aquellas muestras difíciles de predecir o débilmente representadas^^:

$$
\text{FL}(p_t) = -\alpha_t (1 - p_t)^\gamma \log(p_t)
$$

Donde **$p_t$** representa la probabilidad estimada del modelo para el caso real^^. El parámetro de enfoque **$\gamma$** (gamma) controla la agresividad con la que se atenúan las muestras resueltas con alta confianza^^. En la práctica, establecer **$\gamma \in [2.0, 3.0]$** reduce la contribución de pérdida del código limpio y fácil a valores cercanos a cero, permitiendo que las muestras vulnerables —incluso si son muy escasas— dominen el gradiente de optimización sin generar inestabilidades numéricas^^.

* **Class-Balanced Loss (CB)** : Introduce un factor ponderador basado en el concepto del "número efectivo de muestras", en lugar de la proporción inversa bruta^^. El argumento subyacente es que la información de nuevas muestras agregadas a una misma clase tiende a saturarse sintácticamente^^. El término de pérdida CB pondera la pérdida mediante un coeficiente que normaliza la diversidad intrínseca de los datos^^:

$$
\mathcal{L}_{\text{CB}} = \frac{1 - \beta}{1 - \beta^n} \mathcal{L}(p_t)
$$

Donde **$\beta = \frac{N-1}{N}$** regula la tasa de saturación de información sintáctica y **$n$** denota la población total de la clase objetivo^^.

### Implementación Técnica de Pérdida Personalizada en Hugging Face Trainer

La personalización del ciclo de entrenamiento utilizando el marco de trabajo de Hugging Face se logra de manera óptima heredando la clase principal `Trainer` y sobrescribiendo su firma interna de pérdida^^. Esto permite incorporar de forma nativa optimizadores avanzados y flujos de evaluación automatizados^^.

La siguiente clase de PyTorch y Hugging Face implementa un pipeline de optimización robusto que inyecta una versión parametrizada de *Focal Loss* para la detección precisa de vulnerabilidades en código fuente:
