# Target audience and design

The target audience is first-year chemistry students with little to no experience
in theoretical chemistry. Keep UI design and descriptive text intuitive and
simple. Explain necessary technical terms in plain language. Offer additional
details to interested students through optional, expandable explanations, while
keeping the main workflow easy to understand.
Never sacrifice scientific accuracy for simplicity. Simplify the language and
presentation without introducing misconceptions, and make relevant assumptions
and limitations clear.

# Verification

When investigating or fixing a transition-state search failure, run
`pixi run -e dev test-ts`, the opt-in real chemistry regression set. Add a
deterministic case for any newly reported failing molecule. A focused case is
useful during debugging, but run the complete set before finishing and report
any failures. Keep these expensive tests disabled in default test runs.

# Language and terminology

- Use German for student-facing text and address students consistently as “Sie”.
  Keep developer documentation and code identifiers in English.
- Prefer “Übergangszustand” / “transition state” (TS) in the main teaching flow.
  Use “Übergangsstruktur” / “transition structure” specifically for the calculated
  saddle-point geometry, and explain the distinction in optional detail.
- Call the calculated barrier “elektronische Energiebarriere” / “electronic energy
  barrier”, with notation ΔE‡. Do not equate it with Arrhenius activation energy
  or Gibbs energy of activation.
- Distinguish a generated “Startstruktur”, the “Ausgangsstruktur” of a particular
  calculation, and an optimized “Minimum”. A local minimum is not necessarily
  the global minimum; numerical convergence alone does not establish accuracy.
- Distinguish optimization playback, the reaction path, and illustrated molecular
  motions from real-time molecular dynamics. Describe an imaginary frequency by
  its magnitude when comparing it with a numerical threshold.
- Use decimal commas in German prose and figure labels, but preserve machine-readable
  formats (XYZ, CSV, JSON, code). Explain units and abbreviations at first use.
