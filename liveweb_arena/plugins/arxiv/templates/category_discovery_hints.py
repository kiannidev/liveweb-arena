"""Prose hints for locating an arXiv new-submissions stream without naming its official label.

Aligned with CLAUDE.md §3: questions must not embed URLs, selectors, or routing shortcuts.
The agent infers which `/list/<code>/new` page to open from domain knowledge plus browsing.

Keys are arXiv category codes matching `variables.CATEGORIES`.
"""

from typing import Dict

CATEGORY_NAVIGATION_HINTS: Dict[str, str] = {
    "cs.AI": (
        "The computer-science stream where planning, search, and knowledge representation papers "
        "most often land alongside modern learning-based agents."
    ),
    "cs.CL": (
        "The cs area chiefly concerned with human languages, token sequences, and machine "
        "translation or parsing benchmarks."
    ),
    "cs.CV": (
        "The cs track focused on pixels, cameras, detectors, segmentation masks, and visual scenes."
    ),
    "cs.LG": (
        "The cs partition most associated with empirical training loops, generalization, and "
        "differentiable models fit to datasets."
    ),
    "cs.SE": (
        "The cs subject for software lifecycle, repositories, testing practice, and large-scale "
        "engineering studies."
    ),
    "cs.CR": (
        "The cs stream covering protocols, adversaries, proofs about secrecy, and cryptographic constructions."
    ),
    "cs.RO": (
        "The cs listings where manipulation, kinematics, sensing stacks, and autonomous platforms converge."
    ),
    "cs.DS": (
        "The cs class devoted to asymptotic complexity, classical algorithms, and combinatorial structures."
    ),
    "cs.HC": (
        "The cs bucket for usability studies, interaction techniques, and studies of people using interfaces."
    ),
    "cs.IR": (
        "The cs lane for ranking, retrieval metrics, corpora, and query–document modeling."
    ),
    "cs.GT": (
        "The cs niche treating strategic interaction, equilibria, and incentives among rational actors."
    ),
    "math.CO": (
        "The mathematics archive section for enumerative arguments, graphs as discrete objects, and designs."
    ),
    "math.PR": (
        "The math feed centered on stochastic processes, measure-theoretic limits, and random structures."
    ),
    "math.OC": (
        "The math stream about variational problems, controllers, and continuous-time decision systems."
    ),
    "math.NA": (
        "The math area for discretization schemes, floating-point stability, and iterative linear algebra."
    ),
    "math.AG": (
        "The math subject built around varieties, sheaves, and geometric invariants of polynomial systems."
    ),
    "math.AP": (
        "The math queue for PDE well-posedness, Sobolev estimates, and evolution of physical fields."
    ),
    "math.NT": (
        "The math lane for primes, congruences, L-functions, and arithmetic of integers."
    ),
    "math.DG": (
        "The math topic for curvature, bundles, connections, and smooth manifolds beyond Euclidean space."
    ),
    "math.GR": (
        "The math column for symmetries, presentations, and actions of abstract algebraic systems."
    ),
    "hep-th": (
        "The high-energy theory feed discussing strings, dualities, quantum fields, and spacetime models."
    ),
    "hep-ph": (
        "The collider-adjacent phenomenology stream bridging models with signals, rates, and detectors."
    ),
    "quant-ph": (
        "The quantum archive for qubits, channels, entanglement measures, and information-theoretic protocols."
    ),
    "gr-qc": (
        "The archive slice merging classical gravitation with quantum expectations about horizons and cosmology."
    ),
    "astro-ph.CO": (
        "The astrophysics bucket for large-scale structure, dark components, and expansion history."
    ),
    "astro-ph.GA": (
        "The astrophysics lane for stellar populations, galaxies as systems, and interstellar medium interplay."
    ),
    "astro-ph.HE": (
        "The high-energy astrophysics feed for compact objects, relativistic outflows, and energetic spectra."
    ),
    "astro-ph.SR": (
        "The stellar astrophysics listings for interiors, magnetism, and long-lived luminous spheres."
    ),
    "astro-ph.IM": (
        "The astrophysics instrumentation track for telescopes, calibration pipelines, and survey hardware."
    ),
    "cond-mat.str-el": (
        "The condensed-matter stream for strongly correlated lattices, emergent quasiparticles, and phases."
    ),
    "cond-mat.mes-hall": (
        "The mesoscale condensed-matter area for nanowires, quantum dots, and low-dimensional transport."
    ),
    "cond-mat.mtrl-sci": (
        "The materials-facing condensed-matter lane for synthesis, characterization, and structure–property links."
    ),
    "cond-mat.stat-mech": (
        "The many-body equilibrium column for ensembles, phase transitions, and emergent macroscopic laws."
    ),
    "cond-mat.supr-con": (
        "The low-temperature condensed-matter listings for Cooper pairing, Meissner physics, and critical fields."
    ),
    "cond-mat.soft": (
        "The soft matter feed for colloids, gels, active grains, and sluggish thermal motion."
    ),
    "physics.optics": (
        "The physics subject lane for interference, coherence, guided waves, and photonic devices."
    ),
    "stat.ML": (
        "The statistics archive where inference meets high-dimensional prediction and uncertainty for models."
    ),
    "stat.ME": (
        "The statistics methodology lane for estimators, experimental design, and inferential frameworks."
    ),
    "eess.SP": (
        "The electrical-engineering signal stream for filters, spectra, acquisition chains, and discrete transforms."
    ),
    "eess.SY": (
        "The systems-and-control electrical-engineering feed for stability, observers, and feedback synthesis."
    ),
    "eess.AS": (
        "The audio-focused electrical-engineering listings for speech, hearing, and acoustic modeling."
    ),
}
