# Target audience and design

The target audience is first-year chemistry students with little to no experience
in theoretical chemistry. Use a scientific but accessible tone.
Never sacrifice scientific accuracy for simpler wording.

Keep the main workflow concise and easy to follow. State assumptions and
limitations next to a result when they are needed to interpret it correctly.
Put derivations, methodological details, and further explanations in optional,
expandable sections or the student documentation. A short reminder or a reference
is sufficient where the explanation is already available.

Avoid duplicating explanations across UI elements. Tasks state exercises and
required deliverables. Main panels provide essential UI actions and details of
the selected compound or calculation, including brief caveats needed beside a
result. The fundamentals under `site` teach the basics, theory, and concepts that
students are expected to learn before the exercise. Do not teach them again in
the app's collapsible sections. “Methoden und Interpretation” is optional reading
for interested students: demystify how the programs turn inputs into results,
including algorithms, numerical checks, display processing, and implementation-specific
assumptions and limitations. Keep general conceptual explanations on the website;
a short reminder is sufficient when needed to understand a computational detail.

# Verification

When investigating or fixing a transition-structure search failure, run
`pixi run -e dev test-ts`, the opt-in real chemistry regression set. Add a
deterministic case for any newly reported failing molecule. A focused case is
useful during debugging, but run the complete set before finishing and report
any failures. Keep these expensive tests disabled in default test runs.

# Language and terminology

- Use German for student-facing text and address students consistently as “Sie”.
  Keep developer documentation and code identifiers in English.
- Describe UI actions naturally instead of quoting control labels. Refer to the
  structure list, image export, or unit converter by function when guidance is needed.
- Naming the molecules is a student exercise. Generated structure labels should
  show configuration and substitution pattern (for example, “trans · 4-OMe”),
  not the full molecule name. Show calculation status separately as a badge.
- Describe calculations and quantities directly. Avoid playful metaphors,
  anthropomorphizing molecules or algorithms, and rhetorical questions used as
  entertainment. Questions that guide an exercise or identify a help topic are
  appropriate. Use explanatory analogies only when they clarify a concept without
  introducing a misconception.
- Avoid vague language. Name the calculation, quantity, assumption, or limitation
  you mean and explain its practical consequence. Replace generic claims such as
  “meaningful results” or “the model has limitations” with concrete statements.
  Keep uncertainty where scientifically necessary; do not replace it with an
  unsupported promise.
- Use “Übergangsstruktur” / “transition structure” (TS) for the calculated
  saddle-point geometry, its search, validation, and results throughout the app.
  Reserve “Übergangszustand” / “transition state” for the theoretical concept
  and “Übergangszustandstheorie” / “transition-state theory”. Explain the
  distinction once in the fundamentals; do not alternate the terms as synonyms.
- Call the calculated barrier “elektronische Energiebarriere” / “electronic energy
  barrier”, with notation ΔE‡. Do not equate it with Arrhenius activation energy
  or Gibbs energy of activation.
- Distinguish a generated “Startstruktur”, the “Ausgangsstruktur” of a particular
  calculation, and an optimized “Minimumstruktur” / “minimum structure”. Use
  “Minimum” / “minimum” for the mathematical feature of the energy surface,
  as in “lokales Minimum” / “local minimum”, not as a label for a geometry.
  A local minimum is not necessarily the global minimum; numerical convergence
  alone does not establish accuracy.
- Distinguish optimization playback, the reaction path, and illustrated molecular
  motions from real-time molecular dynamics. Describe an imaginary frequency by
  its magnitude when comparing it with a numerical threshold.
- Use decimal commas in German prose and figure labels, but preserve machine-readable
  formats (XYZ, CSV, JSON, code). Assume units are known in the webapp; use unit
  symbols without introducing or defining them. Explain other abbreviations at first use.

# Version control

Commit completed changes after each editing task. Do not push unless the user
explicitly requests it. Keep unrelated user changes out of the commit.
