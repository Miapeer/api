from abc import ABC, abstractclassmethod


class MiapeerRepository(ABC):
    @abstractclassmethod
    def get_all_applications(self):
        pass
