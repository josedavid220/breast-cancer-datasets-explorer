# Cancer Dataset Explorer Project
Reporsitory for a dataset explorer project focused on breast cancer research.

## Installation and usage
1. Install the [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager.
1. Clone the repository:
    ```bash
    git clone https://github.com/josedavid220/breast-cancer-datasets-explorer.git
    ```
1. Download the required datasets and place them in the `data` directory. More info on the datasets can be found in the [data/README.md](data/README.md) file.
1. Install the project dependencies:
    ```bash
    uv sync
    ```
1. Run the application:
    ```bash
    uv run main.py
    ```