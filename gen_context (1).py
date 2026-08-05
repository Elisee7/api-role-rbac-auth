#!/usr/bin/env python3
"""
gen_context.py — Génère (ou met à jour) DEUX fichiers .txt :

  1. context.txt (nom configurable via --output)
     Contexte complet et cumulatif du projet :
       - l'arborescence du projet, FILTRÉE selon la même whitelist que le
         contenu (ne montre que les dossiers/fichiers effectivement extraits)
       - le contenu de chaque fichier concerné, sous la forme :

           #chemin/relatif/fichier.ext
               <contenu indenté>

  2. updated_file.txt (nom configurable via --updated-output)
     Uniquement les fichiers AJOUTÉS ou dont le CONTENU A RÉELLEMENT CHANGÉ
     depuis le dernier run (comparaison octet à octet avec context.txt).
     Ce fichier est TOUJOURS ENTIÈREMENT RÉÉCRIT à chaque exécution (jamais
     fusionné) : il ne reflète que le delta du run en cours.

MODÈLE : LISTE BLANCHE STRICTE.
Seuls les dossiers listés dans --include-dirs et les extensions listées dans
--include-ext sont scannés. Tout le reste est exclu par défaut (y compris
dans l'arborescence affichée).

Un fichier est inclus (dans context.txt, l'arborescence, et potentiellement
updated_file.txt) si :
  - il se trouve dans un dossier listé dans --include-dirs (ou un sous-dossier)
    ET son extension est dans --include-ext
  - OU son chemin exact est listé dans --include-files (fichier précis, inclus
    quelle que soit son extension)
  - OU il se trouve dans un dossier listé dans --include-files (dossier précis,
    tout son contenu est inclus quelle que soit l'extension)

TOUS LES CHEMINS (--include-dirs, --include-files) sont RELATIFS À LA RACINE
DU PROJET (le `root` donné en argument). Utilise "." pour désigner les fichiers
directement à la racine (non récursif sur les autres dossiers).

Comportement de context.txt s'il existe déjà — FUSION (pas de duplication) :
  - l'arborescence est régénérée (toujours à jour)
  - un fichier déjà présent voit son bloc REMPLACÉ par la version actuelle
  - un fichier absent du run précédent est AJOUTÉ
  - un fichier présent avant mais non scanné cette fois est CONSERVÉ tel quel

Comportement de updated_file.txt — TOUJOURS ÉCRASÉ (pas de fusion) :
  - ne contient que les fichiers ajoutés ou modifiés lors de CE run précis
  - un fichier scanné mais dont le contenu est identique au run précédent
    n'y apparaît PAS

Usage :
    python3 gen_context.py . \
        --include-dirs src docs . \
        --include-ext .py .js .md \
        --include-files Dockerfile \
        --output context.txt \
        --updated-output updated_file.txt
"""

import argparse
import os
import re

SECTION_MARKER = "=== CONTENU DES FICHIERS ==="


def norm_rel(path):
    """Normalise un chemin relatif (séparateurs, ./ initiaux)."""
    p = os.path.normpath(path).replace(os.sep, "/")
    return p


def build_tree_filtered(root, include_dirs_set, include_ext, explicit_files, explicit_dirs,
                         prefix="", is_root=True, rel_dir="."):
    """
    Arborescence filtrée selon la même whitelist que le contenu :
    ne montre que les dossiers inclus (ou ancêtres d'un chemin inclus) et les
    fichiers qui seraient effectivement extraits dans le contenu.
    """
    lines = []
    if is_root:
        lines.append(root)
    base_dir = root if rel_dir == "." else os.path.join(root, rel_dir)
    try:
        entries = sorted(os.listdir(base_dir))
    except (PermissionError, FileNotFoundError):
        return "\n".join(lines)

    kept = []
    for entry in entries:
        rel_e = entry if rel_dir == "." else f"{rel_dir}/{entry}"
        full = os.path.join(base_dir, entry)
        if os.path.isdir(full):
            if should_descend(rel_e, include_dirs_set) or any(
                rel_e == ed or rel_e.startswith(ed + "/") for ed in explicit_dirs
            ) or any(ed.startswith(rel_e + "/") for ed in explicit_dirs):
                kept.append((entry, rel_e, True))
        else:
            if file_is_included(rel_dir, entry, rel_e, include_dirs_set, include_ext,
                                 explicit_files, explicit_dirs):
                kept.append((entry, rel_e, False))

    for i, (entry, rel_e, is_dir) in enumerate(kept):
        connector = "└── " if i == len(kept) - 1 else "├── "
        lines.append(prefix + connector + entry)
        if is_dir:
            extension = "    " if i == len(kept) - 1 else "│   "
            sub = build_tree_filtered(root, include_dirs_set, include_ext, explicit_files,
                                       explicit_dirs, prefix + extension, is_root=False, rel_dir=rel_e)
            if sub:
                lines.append(sub)
    return "\n".join(lines)


def is_included_dir(rel_dir, include_dirs_set):
    """Le dossier rel_dir (ou un de ses ancêtres) est-il dans la whitelist ?"""
    if rel_dir in include_dirs_set:
        return True
    return any(rel_dir.startswith(d + "/") for d in include_dirs_set if d != ".")


def should_descend(rel_sub, include_dirs_set):
    """Faut-il continuer à explorer ce sous-dossier (soit inclus, soit ancêtre d'un dossier inclus) ?"""
    if is_included_dir(rel_sub, include_dirs_set):
        return True
    return any(d == rel_sub or d.startswith(rel_sub + "/") for d in include_dirs_set if d != ".")


def file_is_included(rel_dir, filename, rel_file, include_dirs_set, include_ext,
                      explicit_files, explicit_dirs):
    """Logique unique de décision : ce fichier doit-il apparaître (contenu ET tree) ?"""
    ext = os.path.splitext(filename)[1]
    in_included_dir = is_included_dir(rel_dir, include_dirs_set) and ext in include_ext
    matches_explicit_file = rel_file in explicit_files
    matches_explicit_dir = any(
        rel_file == ed or rel_file.startswith(ed + "/") for ed in explicit_dirs
    )
    return in_included_dir or matches_explicit_file or matches_explicit_dir


def resolve_include_files(root, include_files):
    """Sépare --include-files en fichiers explicites et dossiers explicites (chemins normalisés)."""
    explicit_files = set()
    explicit_dirs = set()
    for entry in include_files:
        rel = norm_rel(entry)
        full = os.path.join(root, rel)
        if os.path.isdir(full):
            explicit_dirs.add(rel)
        else:
            explicit_files.add(rel)
    return explicit_files, explicit_dirs


def collect_files(root, include_dirs_set, include_ext, explicit_files, explicit_dirs):
    collected = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = norm_rel(os.path.relpath(dirpath, root))

        pruned = []
        for d in dirnames:
            rel_d = d if rel_dir == "." else f"{rel_dir}/{d}"
            if should_descend(rel_d, include_dirs_set) or any(
                rel_d == ed or rel_d.startswith(ed + "/") for ed in explicit_dirs
            ) or any(ed.startswith(rel_d + "/") for ed in explicit_dirs):
                pruned.append(d)
        dirnames[:] = pruned

        for filename in sorted(filenames):
            rel_file = filename if rel_dir == "." else f"{rel_dir}/{filename}"

            if file_is_included(rel_dir, filename, rel_file, include_dirs_set, include_ext,
                                 explicit_files, explicit_dirs):
                full_path = os.path.join(dirpath, filename)
                collected.append((rel_file, full_path))

    return collected


def render_file_block(rel_path, full_path, indent="    "):
    lines = [f"#{rel_path}\n"]
    try:
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                lines.append(indent + line)
    except OSError as e:
        lines.append(f"{indent}[Erreur de lecture : {e}]\n")
    lines.append("\n\n")
    return "".join(lines)


def parse_existing_entries(output_path):
    if not os.path.exists(output_path):
        return {}

    with open(output_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    if SECTION_MARKER not in content:
        return {}

    files_section = content.split(SECTION_MARKER, 1)[1]

    entries = {}
    header_re = re.compile(r"^#(.+)$", re.MULTILINE)
    matches = list(header_re.finditer(files_section))

    for i, m in enumerate(matches):
        rel_path = m.group(1)
        body_start = m.end() + 1  # saute le \n qui termine la ligne d'en-tête
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(files_section)
        entries[rel_path] = files_section[body_start:body_end]

    return entries


def write_context_file(root, include_dirs, include_ext, include_files, output_path,
                        updated_output_path, indent="    "):
    include_dirs_set = {norm_rel(d) for d in include_dirs}
    explicit_files, explicit_dirs = resolve_include_files(root, include_files)

    tree_output = build_tree_filtered(root, include_dirs_set, include_ext, explicit_files, explicit_dirs)
    files = collect_files(root, include_dirs_set, include_ext, explicit_files, explicit_dirs)

    existing_entries = parse_existing_entries(output_path)
    was_existing = os.path.exists(output_path)

    added_list = []
    modified_list = []
    unchanged = 0

    for rel_path, full_path in files:
        block = render_file_block(rel_path, full_path, indent)
        body = block.split("\n", 1)[1]
        if rel_path in existing_entries:
            if existing_entries[rel_path] != body:
                modified_list.append((rel_path, body))
            else:
                unchanged += 1
        else:
            added_list.append((rel_path, body))
        existing_entries[rel_path] = body

    # --- context.txt : fusion complète, sans doublons ---
    with open(output_path, "w", encoding="utf-8") as out:
        out.write("=== ARBORESCENCE DU PROJET ===\n\n")
        out.write(tree_output)
        out.write("\n\n" + SECTION_MARKER + "\n\n")
        for rel_path in sorted(existing_entries):
            out.write(f"#{rel_path}\n")
            out.write(existing_entries[rel_path])

    # --- updated_file.txt : uniquement les fichiers nouveaux ou dont le contenu a changé ---
    # Toujours écrasé (pas de fusion) : reflète uniquement CE run.
    updated_entries = added_list + modified_list
    with open(updated_output_path, "w", encoding="utf-8") as uf:
        if updated_entries:
            uf.write("=== FICHIERS AJOUTÉS OU MODIFIÉS LORS DE CE RUN ===\n\n")
            for rel_path, body in sorted(updated_entries, key=lambda x: x[0]):
                uf.write(f"#{rel_path}\n")
                uf.write(body)
        else:
            uf.write("Aucun fichier ajouté ou modifié lors de ce run.\n")

    kept_untouched = len(existing_entries) - len(added_list) - len(modified_list) - unchanged
    action = "mis à jour (fusion)" if was_existing else "créé"
    print(f"Fichier de contexte {action} : {output_path}")
    print(f"  Ajoutés            : {len(added_list)}")
    print(f"  Modifiés           : {len(modified_list)}")
    print(f"  Inchangés          : {unchanged}")
    print(f"  Conservés (non scannés cette fois) : {kept_untouched}")
    print(f"  Total dans le fichier : {len(existing_entries)}")
    print(f"Fichier des changements écrit : {updated_output_path} ({len(updated_entries)} fichier(s))")


def main():
    parser = argparse.ArgumentParser(
        description="Génère ou met à jour un contexte texte d'une codebase (liste blanche stricte, fusion sans doublons)."
    )
    parser.add_argument("root", nargs="?", default=".", help="Dossier racine du projet (défaut: .)")
    parser.add_argument(
        "--include-dirs",
        nargs="+",
        required=True,
        help="Dossiers à inclure (whitelist), chemins relatifs à la racine. "
             "Utilise '.' pour les fichiers directement à la racine. Ex: src docs .",
    )
    parser.add_argument(
        "--include-ext",
        nargs="+",
        required=True,
        help="Extensions à inclure (whitelist), ex: .py .js .ts .html .md",
    )
    parser.add_argument(
        "--include-files",
        nargs="*",
        default=[],
        help="Fichiers ou dossiers précis à inclure en plus, quelle que soit l'extension. "
             "Chemins relatifs à la racine, ex: Dockerfile docs/CHANGELOG",
    )
    parser.add_argument(
        "--output",
        default="codebase_context.txt",
        help="Nom du fichier de sortie (défaut: codebase_context.txt). Si le fichier existe, fusion sans doublons.",
    )
    parser.add_argument(
        "--updated-output",
        default="updated_file.txt",
        help="Nom du fichier listant uniquement les fichiers ajoutés/modifiés à ce run "
             "(défaut: updated_file.txt). Toujours écrasé, jamais fusionné.",
    )
    args = parser.parse_args()

    include_dirs = [norm_rel(d) for d in args.include_dirs]
    include_ext = {e if e.startswith(".") else f".{e}" for e in args.include_ext}

    write_context_file(args.root, include_dirs, include_ext, args.include_files,
                        args.output, args.updated_output)


if __name__ == "__main__":
    main()
