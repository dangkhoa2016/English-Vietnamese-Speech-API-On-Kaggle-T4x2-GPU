# Real-model acceptance

These checks require a Kaggle GPU T4 x2 session and attached local model inputs.
They are intentionally excluded from CPU-only pytest/CI.

## TranslateGemma GPU 0

Run `scripts/smoke_translation.sh`.

PASS requires:

- physical GPU 0 only is visible to the translation process;
- JAX reports exactly one logical GPU;
- the local TranslateGemma 4B IT preset loads without network downloads;
- a fixed English sentence produces non-empty Vietnamese text;
- physical GPU 1 receives no TranslateGemma/JAX allocation;
- the worker exits cleanly and GPU memory returns to baseline.
