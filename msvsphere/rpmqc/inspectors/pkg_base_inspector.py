import abc

from msvsphere.rpmqc.config import Config
from msvsphere.rpmqc.reporter import ReporterTap
from msvsphere.rpmqc.rpm_package import RPMPackage

__all__ = ['Config', 'PkgBaseInspector', 'ReporterTap', 'RPMPackage']


class PkgBaseInspector(abc.ABC):

    @abc.abstractmethod
    def __init__(self, cfg: Config):
        pass

    @abc.abstractmethod
    def inspect(self, pkg: RPMPackage, reporter: ReporterTap):
        pass
