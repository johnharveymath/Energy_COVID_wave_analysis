import os
from dataclasses import dataclass, field


@dataclass
class Config:
    base_path: str = None
    plot_path: str = field(init=False)
    data_path: str = field(init=False)
    cache_path: str = field(init=False)

    def __post_init__(self):
        if not self.base_path:
            return

        self.plot_path = os.path.abspath(
            os.path.join(self.base_path, "../plots")
        )
        self.data_path = os.path.abspath(os.environ["COVID_DATA_PATH"])

        print(self.base_path)
        print(self.plot_path)
        print(self.data_path)