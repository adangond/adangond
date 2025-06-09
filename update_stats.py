import os
import requests
import datetime
import re

# Obtén el token de GitHub desde las variables de entorno
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("GITHUB_TOKEN no encontrado en las variables de entorno.")
    exit(1)

headers = {"Authorization": f"token {GITHUB_TOKEN}"}

# Calcula la fecha de hace 7 días (en formato ISO)
today = datetime.datetime.utcnow()
since_dt = today - datetime.timedelta(days=7)
since_iso = since_dt.isoformat() + "Z"

# URL para obtener todos tus repositorios (públicos y privados)
repos_url = "https://api.github.com/user/repos?per_page=100&affiliation=owner,collaborator,organization_member"
response = requests.get(repos_url, headers=headers)
if response.status_code != 200:
    print("Error al obtener repositorios:", response.status_code)
    exit(1)

repos = response.json()

# Lista para almacenar las filas de la tabla (repositorio, commits, último push)
rows = []
for repo in repos:
    repo_name = repo.get("name")
    owner = repo.get("owner", {}).get("login")
    # Consulta el endpoint de commits en el repositorio desde hace 7 días (asumimos menos de 100 commits)
    commits_url = f"https://api.github.com/repos/{owner}/{repo_name}/commits?since={since_iso}&per_page=100"
    commits_response = requests.get(commits_url, headers=headers)
    if commits_response.status_code != 200:
        # Si hay un error, omitimos el repositorio
        continue
    commits = commits_response.json()
    commit_count = len(commits)
    if commit_count > 0:
        # Extraemos la última fecha de push (se puede formatear para mayor claridad)
        pushed_at = repo.get("pushed_at", "")
        last_push = pushed_at.split("T")[0] if pushed_at else "N/A"
        rows.append((repo_name, commit_count, last_push))

# Construye la tabla en Markdown
stats_md = "Esta tabla muestra la actividad en tus repositorios de los últimos 7 días.\n\n"
stats_md += f"Consultado el: {today.strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"

if rows:
    stats_md += "| Repositorio | Commits en últimos 7 días | Último push |\n"
    stats_md += "|-------------|---------------------------:|------------:|\n"
    # Ordena de mayor a menor cantidad de commits
    rows.sort(key=lambda x: x[1], reverse=True)
    for repo_name, count, push_date in rows:
        stats_md += f"| {repo_name} | {count} | {push_date} |\n"
else:
    stats_md += "No se encontraron commits en los últimos 7 días.\n"

# Abrir el archivo README.md y actualizar la sección marcada con <!--GITHUB_STATS:start-->
readme_file = "README.md"
try:
    with open(readme_file, "r", encoding="utf-8") as f:
        content = f.read()
except Exception as e:
    print("Error al abrir README.md:", e)
    exit(1)

# Expresión regular para reemplazar el bloque entre los marcadores
pattern = r"(<!--GITHUB_STATS:start-->)(.*?)(<!--GITHUB_STATS:end-->)"
replacement = f"<!--GITHUB_STATS:start-->\n{stats_md}\n<!--GITHUB_STATS:end-->"
new_content, num_subs = re.subn(pattern, replacement, content, flags=re.DOTALL)

if num_subs == 0:
    print("No se encontró la sección marcada en el README.")
else:
    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("README actualizado exitosamente con las estadísticas semanales.")
