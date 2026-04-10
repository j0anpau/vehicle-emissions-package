from .api import (
    build_df_merged_final,
    build_df_merged_final_from_config,
    build_stream_a_dataframe,
    build_stream_b_dataframe,
    get_default_model_config,
    resolve_model_config,
)

# Convenience alias for a cleaner import path
df_lifecycle = build_df_merged_final

__all__ = [
    "build_df_merged_final",
    "build_df_merged_final_from_config",
    "build_stream_a_dataframe",
    "build_stream_b_dataframe",
    "get_default_model_config",
    "resolve_model_config",
    "df_lifecycle",
]
