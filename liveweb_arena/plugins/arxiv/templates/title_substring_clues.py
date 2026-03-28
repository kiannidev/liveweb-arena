"""(clue, needle) pairs: substring audit without spelling the needle in the clue (case-insensitive)."""

from typing import List, Tuple

TITLE_SUBSTRING_SPECS: List[Tuple[str, str]] = [
    ("Vertices-and-edges structures in discrete mathematics", "graph"),
    ("Checkpoint artifact saved after training steps", "model"),
    ("Tabular measurements fed into pipelines", "data"),
    ("Stochastic optimization on differentiable surfaces", "loss"),
    ("Discipline concerned with estimators and populations", "stat"),
    ("Physical quantity that can interfere constructively", "wave"),
    ("Astronomical point source often studied in binaries", "star"),
    ("Dense rectangular array used in linear maps", "matrix"),
    ("Unit of language smaller than a sentence", "token"),
    ("Operation that slides kernels over a grid", "conv"),
    ("Unobserved variables in hierarchical Bayes", "latent"),
    ("Opposite of sparse in parameterization", "dense"),
    ("Small additive perturbation used in attacks", "noise"),
    ("Function shaping outputs to a simplex", "softmax"),
    ("Iterated refinement of internal representations", "layer"),
    ("Pass over the full dataset during fitting", "epoch"),
    ("Subset drawn without replacement for updates", "batch"),
    ("Mechanism that randomly zeros activations", "dropout"),
    ("Shortcut connection merging signals additively", "residual"),
    ("Scaling activations to zero mean near layers", "batchnorm"),
    ("Drawing examples from a proposal distribution", "sampling"),
    ("Spread of a random variable around its mean", "variance"),
    ("Joint second-moment structure between coordinates", "covariance"),
    ("Relative support data gives for parameters", "likelihood"),
    ("Belief after seeing measurements", "posterior"),
    ("Belief before seeing measurements", "prior"),
    ("Density obtained after collapsing nuisance coordinates onto a smaller set", "marginal"),
    ("Antiderivative viewpoint on accumulation", "integral"),
    ("Infinitesimal change along a smooth path", "differential"),
    ("Energy operator in many conservative systems", "hamiltonian"),
    ("Principle stationary paths extremize action", "lagrangian"),
    ("Topological space patched like Euclidean space", "manifold"),
    ("Measure of how a path bends in space", "curvature"),
    ("Oscillator studied in introductory quantum courses", "harmonic"),
    ("Potential barrier penetration without classical energy", "tunneling"),
    ("Orthonormal directions spanning outcomes of a sharp observable", "basis"),
    ("Non-classical correlations stronger than mixture models", "entangle"),
    ("Two-dimensional projection of scattering results", "dalitz"),
    ("Scaling violation in deep inelastic scattering", "bjorken"),
    ("Effective description of Goldstone modes", "chiral"),
    ("Color charge trapped inside hadrons in gauge theories", "confinement"),
    ("Background of relic photons from early universe", "cmb"),
    ("Metric describing spatially homogeneous expansion", "friedmann"),
    ("Compact object lighter than a neutron star but dark", "black"),
    ("Stellar explosion leaving compact remnant", "supernova"),
    ("Gravitational waveform from merging binaries", "chirp"),
    ("Accretion flow around compact objects", "disk"),
    ("Polarized emission from ordered fields", "synchrotron"),
    ("Shock-heated plasma in cluster mergers", "intracluster"),
]


def _validate_specs() -> None:
    for clue, needle in TITLE_SUBSTRING_SPECS:
        if needle.lower() in clue.lower():
            raise ValueError(f"Clue leaks needle {needle!r}: {clue!r}")


_validate_specs()
