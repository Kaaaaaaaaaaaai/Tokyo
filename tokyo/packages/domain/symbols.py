import hashlib

from tokyo.packages.contracts.enums import Universe, Variant


class SymbolIdGenerator:
    """Stable MVP symbol ID generator with room for future long-form IDs."""

    def generate(
        self,
        *,
        universe: Universe,
        variant: Variant,
        asset: str,
        quote_asset: str | None,
        unit: str,
    ) -> str:
        material = "|".join(
            [universe.value, variant.value, asset.upper(), (quote_asset or "").upper(), unit.upper()]
        )
        digest = hashlib.blake2s(material.encode("utf-8"), digest_size=4).hexdigest()
        return digest.upper()

