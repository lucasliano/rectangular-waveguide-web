"""
Guía de onda rectangular en Ansys HFSS
Cátedra de Medios de Enlace · UTN.BA · Autor: Lucas Liaño

Construye en HFSS la guía de onda del sitio web: tubo de aire de a × b × L con
paredes de cobre, un puerto de onda en cada extremo y el setup de simulación
listo para comparar con las curvas y los campos analíticos del sitio.

Requisitos
  * Ansys Electronics Desktop (la versión estudiantil gratuita alcanza).
  * Python 3.10 o posterior y PyAEDT:   pip install pyaedt

Uso (los valores por defecto son los del sitio: a = 20 mm, b = 10 mm, L = 100 mm)
  python guia_onda_hfss.py                     solo construye el modelo y lo deja abierto
  python guia_onda_hfss.py --a 25 --b 10       otra sección transversal
  python guia_onda_hfss.py --resolver          además resuelve y arma los gráficos
  python guia_onda_hfss.py --fmax 30 --campos 10 20 --resolver
  python guia_onda_hfss.py --help              todas las opciones

Qué queda en el proyecto
  * Variables a, b, L (se pueden cambiar desde HFSS > Design Properties).
  * Puertos P1 (z = 0) y P2 (z = L), con tantos modos como se propagan hasta fmax.
  * Setup: malla adaptativa a fmax, barrido interpolante de fmin a fmax ("Barrido")
    y barrido discreto con campos guardados ("Campos").
  * Con --resolver: S21, β = Im γ y α = Re γ de cada modo (comparar con la
    sección Dispersión) y |E| en tres cortes del sistema "centro" (comparar con
    el explorador de campos y los cortes de la sección Modos).
"""

import argparse
import math
import os
import sys

C0 = 299792458.0


def modos_hasta(a_mm, b_mm, fmax_ghz):
    """Modos TE/TM con frecuencia de corte por debajo de fmax, ordenados por corte."""
    a, b = a_mm / 1000, b_mm / 1000
    out = []
    for m in range(0, 15):
        for n in range(0, 15):
            if m == 0 and n == 0:
                continue
            fc = C0 / 2 * math.hypot(m / a, n / b) / 1e9
            if fc < fmax_ghz:
                out.append((fc, f"TE{m}{n}"))
                if m and n:
                    out.append((fc, f"TM{m}{n}"))
    return sorted(out)


def argumentos():
    p = argparse.ArgumentParser(description="Guía de onda rectangular en HFSS (Medios de Enlace, UTN.BA)")
    p.add_argument("--a", type=float, default=20.0, help="pared ancha a en mm (por defecto 20)")
    p.add_argument("--b", type=float, default=10.0, help="pared angosta b en mm (por defecto 10)")
    p.add_argument("--L", type=float, default=100.0, help="largo L en mm (por defecto 100)")
    p.add_argument("--fmin", type=float, default=2.5, help="inicio del barrido en GHz (por defecto 2.5)")
    p.add_argument("--fmax", type=float, default=26.0, help="fin del barrido y frecuencia de la malla adaptativa en GHz (por defecto 26, como el gráfico de Dispersión)")
    p.add_argument("--campos", type=float, nargs="+", default=[10.0], help="frecuencias en GHz con campos guardados (por defecto 10)")
    p.add_argument("--modos", type=int, default=0, help="modos por puerto (por defecto, todos los que se propagan hasta fmax)")
    p.add_argument("--excitar", type=int, default=1, help="modo del puerto 1 excitado para los campos (1 = el de menor corte, el TE10)")
    p.add_argument("--resolver", action="store_true", help="resolver y crear los gráficos")
    p.add_argument("--nucleos", type=int, default=4, help="núcleos para resolver (por defecto 4)")
    p.add_argument("--version", default=None, help="versión de AEDT, por ejemplo 2025.1 (por defecto, la más nueva instalada)")
    p.add_argument("--licencia", choices=["estudiantil", "completa"], default="estudiantil", help="edición de AEDT instalada")
    p.add_argument("--sin-interfaz", action="store_true", help="correr AEDT sin ventana y cerrarlo al terminar")
    p.add_argument("--carpeta", default=".", help="carpeta donde se guarda el proyecto (por defecto, la actual)")
    return p.parse_args()


def puerto(hfss, nombre, cara, a, b, z, n_modos):
    """Puerto de onda con n_modos modos y alineación analítica: los pares degenerados
    TE_mn / TM_mn salen como modos TE y TM puros, igual que en las fórmulas del sitio."""
    modos = ["NAME:Modes"] + [["NAME:Mode%d" % k, "ModeNum:=", k, "UseIntLine:=", False,
                               "AlignmentGroup:=", 0, "CharImp:=", "Zpi"] for k in range(1, n_modos + 1)]
    hfss.oboundary.AssignWavePort([
        "NAME:" + nombre, "Faces:=", [cara], "NumModes:=", n_modos, "UseLineModeAlignment:=", False,
        "DoDeembed:=", False, "RenormalizeAllTerminals:=", False, modos,
        "UseAnalyticAlignment:=", True,
        ["NAME:AnalyticULine", "Start:=", [f"{a}mm", f"{b / 2}mm", z], "End:=", ["0mm", f"{b / 2}mm", z]],
        "AnalyticReverseV:=", False, "ShowReporterFilter:=", False, "ReporterFilter:=", [True] * n_modos])


def construir(hfss, o, n_modos):
    md = hfss.modeler
    md.model_units = "mm"
    hfss["a"], hfss["b"], hfss["L"] = f"{o.a}mm", f"{o.b}mm", f"{o.L}mm"
    # el interior de la guía: x en [0, a], y en [0, b], z en [0, L], como en el sitio
    guia = md.create_box([0, 0, 0], ["a", "b", "L"], name="guia", material="vacuum")
    p1, p2 = guia.bottom_face_z.id, guia.top_face_z.id
    puerto(hfss, "P1", p1, o.a, o.b, "0mm", n_modos)
    puerto(hfss, "P2", p2, o.a, o.b, f"{o.L}mm", n_modos)
    # las otras cuatro caras son las paredes: cobre de conductividad finita (σ = 5,8e7 S/m)
    hfss.assign_finite_conductivity([f.id for f in guia.faces if f.id not in (p1, p2)], material="copper", name="paredes")
    # semilla de malla: un tercio de la longitud de onda a fmax. La malla adaptativa refina el resto.
    lam = C0 / (o.fmax * 1e9) * 1000
    hfss.mesh.assign_length_mesh([guia.name], maximum_length=min(4.0, lam / 3), maximum_elements=None, name="semilla")
    # sistema de coordenadas en el centro de la guía: sus planos XY, XZ e YZ son los cortes del sitio
    md.create_coordinate_system(origin=["a/2", "b/2", "L/2"], name="centro")
    md.set_working_coordinate_system("Global")
    setup = hfss.create_setup("Setup", Frequency=f"{o.fmax}GHz", MaximumPasses=12, MinimumPasses=2,
                              MinimumConvergedPasses=2, MaxDeltaS=0.02)
    n = int(round((o.fmax - o.fmin) / 0.125)) + 1
    setup.create_frequency_sweep(unit="GHz", name="Barrido", start_frequency=o.fmin, stop_frequency=o.fmax,
                                 num_of_freq_points=n, sweep_type="Interpolating", save_fields=False,
                                 interpolation_tol=0.5, interpolation_max_solutions=250)
    setup.create_single_point_sweep(unit="GHz", freq=list(o.campos), save_fields=True, name="Campos")
    # excitación para los campos: solo el modo elegido del puerto 1, con 1 W
    fuentes = {f"P1:{k}": ("1W" if k == o.excitar else "0W", "0deg") for k in range(1, n_modos + 1)}
    fuentes.update({f"P2:{k}": ("0W", "0deg") for k in range(1, n_modos + 1)})
    hfss.edit_sources(fuentes)
    hfss.save_project()


def graficos(hfss, o, modos):
    post = hfss.post
    barrido = "Setup : Barrido"
    post.create_report(expressions=["dB(S(P2:1,P1:1))"], setup_sweep_name=barrido, domain="Sweep",
                       primary_sweep_variable="Freq", plot_name="S21 del modo 1 (dB)")
    # γ = α + jβ de cada modo del puerto 1 (HFSS lo llama Gamma), para comparar con la sección Dispersión
    k = range(1, len(modos) + 1)
    post.create_report(expressions=[f"im(Gamma(P1:{i}))" for i in k], setup_sweep_name=barrido, domain="Sweep",
                       primary_sweep_variable="Freq", plot_name="beta = Im(gamma) (rad/m)")
    post.create_report(expressions=[f"re(Gamma(P1:{i}))*8.686" for i in k], setup_sweep_name=barrido, domain="Sweep",
                       primary_sweep_variable="Freq", plot_name="alfa = Re(gamma) (dB/m)")
    for f in o.campos:
        for plano in ("XZ", "YZ", "XY"):
            post.create_fieldplot_cutplane(assignment=[f"centro:{plano}"], quantity="Mag_E", setup="Setup : Campos",
                                           intrinsics={"Freq": f"{f:g}GHz", "Phase": "0deg"},
                                           plot_name=f"E_{plano}_{f:g}GHz")
    carpeta = os.path.dirname(hfss.project_file)
    hfss.export_touchstone(setup="Setup", sweep="Barrido",
                           output_file=os.path.join(carpeta, f"{hfss.design_name}.s{2 * len(modos)}p"))


def main():
    o = argumentos()
    try:
        from ansys.aedt.core import Hfss
    except ImportError:
        sys.exit('Falta PyAEDT. Instalalo con:  pip install pyaedt')
    if o.b > o.a:
        sys.exit("Por convención a es la pared ancha: usá a >= b.")

    modos = modos_hasta(o.a, o.b, o.fmax)
    n_modos = o.modos or max(1, len(modos))
    if not 1 <= o.excitar <= n_modos:
        sys.exit(f"--excitar debe estar entre 1 y {n_modos}.")
    print(f"Guía de {o.a:g} × {o.b:g} × {o.L:g} mm, barrido {o.fmin:g}–{o.fmax:g} GHz")
    print(f"Modos que se propagan hasta {o.fmax:g} GHz ({n_modos} por puerto): "
          + ", ".join(f"{nm} ({fc:.2f} GHz)" for fc, nm in modos[:n_modos]))
    if n_modos > 12:
        print("Aviso: muchos modos por puerto hacen la simulación más pesada. Si la versión estudiantil "
              "se queda corta, bajá --fmax o achicá --L.")

    nombre = f"guia_a{o.a:g}_b{o.b:g}".replace(".", "p")
    os.makedirs(o.carpeta, exist_ok=True)
    proyecto = os.path.abspath(os.path.join(o.carpeta, nombre + ".aedt"))
    hfss = Hfss(project=proyecto, design=nombre, solution_type="Modal", version=o.version,
                non_graphical=o.sin_interfaz, new_desktop=True, student_version=o.licencia == "estudiantil")
    try:
        if "guia" in hfss.modeler.object_names:
            print("El proyecto ya tenía la guía: se usa tal cual (borralo para empezar de cero).")
        else:
            construir(hfss, o, n_modos)
            print(f"Modelo listo: {proyecto}")
        if o.resolver:
            print("Resolviendo (puede tardar algunos minutos)...")
            if not hfss.analyze_setup("Setup", cores=o.nucleos):
                sys.exit("HFSS no pudo resolver el setup: revisá la ventana de mensajes de AEDT.")
            graficos(hfss, o, modos[:n_modos])
            hfss.save_project()
            print("Listo: los gráficos están en Results y Field Overlays del árbol del proyecto.")
        else:
            print("Para resolver: Analyze All en HFSS, o volvé a correr el script con --resolver.")
    finally:
        # con interfaz, AEDT queda abierto para explorar el modelo
        hfss.release_desktop(close_projects=o.sin_interfaz, close_desktop=o.sin_interfaz)
    return 0


if __name__ == "__main__":
    sys.exit(main())
