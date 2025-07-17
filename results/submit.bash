#!/bin/bash

for XC in LDA PBE BLYP PBE0 B3LYP; do
    for BASIS in STO-3G def2-SVP def2-TZVP; do
        for SUB in H F Cl OH OMe NH2 NMe2 NO2; do
           sbatch --job-name="uvvis" --time=01:00:00 --mem-per-cpu=8000M --wrap="pixi run python3 uvvis.py --xc=$XC --basis=$BASIS --r1c1=$SUB"
           sbatch --job-name="uvvis" --time=01:00:00 --mem-per-cpu=8000M --wrap="pixi run python3 uvvis.py --xc=$XC --basis=$BASIS --r1c2=$SUB"
           sbatch --job-name="uvvis" --time=01:00:00 --mem-per-cpu=8000M --wrap="pixi run python3 uvvis.py --xc=$XC --basis=$BASIS --r1c3=$SUB"
           sbatch --job-name="uvvis" --time=01:00:00 --mem-per-cpu=8000M --wrap="pixi run python3 uvvis.py --xc=$XC --basis=$BASIS --r1c4=$SUB"
           sbatch --job-name="uvvis" --time=01:00:00 --mem-per-cpu=8000M --wrap="pixi run python3 uvvis.py --xc=$XC --basis=$BASIS --r1c5=$SUB"
        done
    done
done
