from dataclasses import dataclass


@dataclass
class Application:
    id: str = ""
    name: str = ""
    url: str = ""
    description: str = ""
    icon: str = ""
    display: bool = False
