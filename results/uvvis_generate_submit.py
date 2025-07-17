import achprak

xc_functionals = ["BLYP", "B3LYP", "CAM-B3LYP"]
basis_sets = ["def2-SVP", "def2-TZVP", "6-31G(d)", "6-31G(d,p)"]
substitutions = achprak.azobenzene.Template.substituent_smiles.keys()

position_flags = []
for i in range(1, 6):
    position_flags.append((f"--r1c{i}",))
    position_flags.append((f"--r1c{i}", f"--r2c{i}"))

args = []
for xc in xc_functionals:
    for basis in basis_sets:
        for sub in substitutions:
            for flags in position_flags:
                arg_list = [f"--xc={xc}", f"--basis={basis}"]
                arg_list += [f"{flag}={sub}" for flag in flags]
                args.append(" ".join(arg_list))

script = f"""\
#!/bin/bash
#SBATCH --job-name=uvvis
#SBATCH --time=01:00:00
#SBATCH --mem-per-cpu=8000M
#SBATCH --array=0-{len(args)}
#SBATCH --output=logs/uvvis_%A_%a.out
#SBATCH --error=logs/uvvis_%A_%a.err

ARGS=(
    {"\n".join(["'" + arg + "'" for arg in args])}
)

exec pixi run python3 uvvis_standalone.py "${{ARGS[SLURM_ARRAY_TASK_ID]}}"
"""

print(script)
