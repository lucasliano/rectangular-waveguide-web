# Guía de onda rectangular · Medios de Enlace (UTN.BA)

Sitio web didáctico sobre la guía de onda rectangular, para la cátedra de Medios de Enlace de la UTN.BA.
Muestra campos, modos y dispersión de una guía llena de aire con paredes de cobre, y explica cómo
reproducir los resultados en Ansys HFSS.

Todo lo que muestra el sitio se calcula en el navegador a partir de las expresiones analíticas:
no hay datos precalculados ni servidor. Es un sitio estático listo para GitHub Pages.

## Contenido

| Ruta | Qué es |
|---|---|
| `index.html` | El sitio completo (HTML, CSS y JavaScript en un solo archivo). Secciones: campos (explorador 3D, WebGL2), modos, dispersión, modelo y simulación. |
| `lang/en.js` | Traducción al inglés. Se elige con el selector de idioma o con `?lang=en` en la URL. |
| `descargas/guia_onda_hfss.py` | Script de PyAEDT que se descarga desde el sitio: arma en HFSS la misma guía (variables `a`, `b`, `L`, puertos, setup) y, con `--resolver`, la resuelve y genera los gráficos para comparar. |
| `estilo/` | Copia de los tokens del sistema de diseño GIAR · UTN.BA (colores, tipografía, espaciado y logo). No se editan acá; ver `estilo/README.md`. |

Bibliotecas externas cargadas desde CDN: [Plotly](https://plotly.com/javascript/) 2.27.0 (gráficos)
y [MathJax](https://www.mathjax.org/) 3.2.2 (ecuaciones). Las fuentes vienen de Google Fonts.

## Verlo en local

Alcanza con abrir `index.html` en el navegador. Como alternativa, un servidor estático:

```sh
python -m http.server 8000
# http://localhost:8000
```

## Publicar en GitHub Pages

1. Subir el repositorio a GitHub.
2. En *Settings → Pages*, elegir *Deploy from a branch*, rama `main`, carpeta `/ (root)`.
3. El sitio queda en `https://<usuario>.github.io/<repositorio>/`.

El archivo `.nojekyll` hace que GitHub sirva los archivos tal cual, sin pasarlos por Jekyll.

## Script de HFSS

Requiere Ansys Electronics Desktop (alcanza la versión estudiantil) y Python 3.10 o posterior con PyAEDT:

```sh
pip install pyaedt
python descargas/guia_onda_hfss.py --help
```

## Autor

Lucas Liaño · GIAR, UTN.BA
