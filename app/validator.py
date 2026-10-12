"""Validate GoodbyeDPI command-line arguments."""

# Flags that take no value
_FLAGS_NO_VALUE = frozenset({
    "-p", "-q", "-r", "-s", "-m", "-n", "-a", "-w",
    "--dns-verb", "--wrong-chksum", "--wrong-seq",
    "--native-frag", "--reverse-frag", "--allow-no-sni",
    "--frag-by-sni",
})

# Flags that require a value after them
_FLAGS_WITH_VALUE = frozenset({
    "-f", "-k", "-e",
    "--port", "--ip-id", "--dns-addr", "--dns-port",
    "--dnsv6-addr", "--dnsv6-port", "--blacklist",
    "--set-ttl", "--min-ttl", "--fake-from-hex",
    "--fake-with-sni", "--fake-gen", "--fake-resend",
})

# Flags whose value is optional
_FLAGS_OPTIONAL_VALUE = frozenset({
    "--auto-ttl", "--max-payload",
})

# Mode shortcuts
_MODESETS = frozenset({
    "-1", "-2", "-3", "-4", "-5", "-6", "-7", "-8", "-9",
})


def _looks_like_value(tok: str) -> bool:
    """Return True if `tok` should be treated as a flag value.

    A token is a value if it does not start with '-' OR it parses as a
    number (this covers negative values such as ``--port -1``, which the
    old validator misclassified as a modeset).
    """
    if not tok.startswith("-"):
        return True
    try:
        float(tok)
        return True
    except ValueError:
        return False


class ValidationResult:
    """Outcome of validating a custom arguments string."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)

    @property
    def is_clean(self) -> bool:
        return not self.errors and not self.warnings


def validate_args(args_str: str) -> ValidationResult:
    """Validate a GoodbyeDPI argument string.

    Returns a ValidationResult with `errors` and `warnings`.
    Empty input yields a clean result.
    """
    result = ValidationResult()
    if not args_str or not args_str.strip():
        return result

    tokens = args_str.split()
    seen: set[str] = set()
    modesets: list[str] = []

    i = 0
    n = len(tokens)

    while i < n:
        tok = tokens[i]

        if not tok.startswith("-"):
            result.errors.append(f"Unexpected value: '{tok}'")
            i += 1
            continue

        if tok in _MODESETS:
            modesets.append(tok)
            seen.add(tok)
            i += 1
            continue

        if tok in _FLAGS_NO_VALUE:
            seen.add(tok)
            i += 1
            continue

        if tok in _FLAGS_WITH_VALUE:
            seen.add(tok)
            if i + 1 < n and _looks_like_value(tokens[i + 1]):
                i += 2
            else:
                result.errors.append(f"'{tok}' requires a value")
                i += 1
            continue

        if tok in _FLAGS_OPTIONAL_VALUE:
            seen.add(tok)
            if i + 1 < n and _looks_like_value(tokens[i + 1]):
                i += 2
            else:
                i += 1
            continue

        result.errors.append(f"Unknown flag: '{tok}'")
        i += 1

    # ---------------- Cross-flag checks ----------------
    if len(modesets) > 1:
        result.warnings.append(
            f"Multiple modesets combined: {', '.join(modesets)}"
        )

    if modesets and (len(seen) > len(modesets)):
        result.warnings.append(
            "Mixing a modeset with individual flags may behave unexpectedly"
        )

    if "-n" in seen and "-k" not in seen:
        result.warnings.append("'-n' has no effect without '-k'")

    if "-a" in seen and "-s" in seen:
        result.warnings.append("'-a' already enables '-s' (redundant)")

    if ("--min-ttl" in seen
            and "--set-ttl" not in seen
            and "--auto-ttl" not in seen):
        result.warnings.append(
            "'--min-ttl' has no effect without '--set-ttl' or '--auto-ttl'"
        )

    if "--dns-port" in seen and "--dns-addr" not in seen:
        result.warnings.append(
            "'--dns-port' has no effect without '--dns-addr'"
        )

    if "--dnsv6-port" in seen and "--dnsv6-addr" not in seen:
        result.warnings.append(
            "'--dnsv6-port' has no effect without '--dnsv6-addr'"
        )

    fake_modes = {"--wrong-seq", "--wrong-chksum", "--set-ttl", "--auto-ttl"}
    active = fake_modes & seen
    if len(active) > 1:
        result.warnings.append(
            f"Multiple fake request modes active: {', '.join(sorted(active))}"
        )

    return result