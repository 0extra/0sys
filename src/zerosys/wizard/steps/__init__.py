from __future__ import annotations

from zerosys.wizard.steps.base import WizardState, WizardStep
from zerosys.wizard.steps.choose_role import ChooseRoleStep
from zerosys.wizard.steps.packages import PackagesStep
from zerosys.wizard.steps.review import ReviewStep
from zerosys.wizard.steps.security import SecurityStep
from zerosys.wizard.steps.server_info import ServerInfoStep
from zerosys.wizard.steps.services import ServicesStep
from zerosys.wizard.steps.ssh_setup import SshSetupStep
from zerosys.wizard.steps.users import UsersStep
from zerosys.wizard.steps.welcome import WelcomeStep

__all__ = [
    "ChooseRoleStep",
    "PackagesStep",
    "ReviewStep",
    "SecurityStep",
    "ServerInfoStep",
    "ServicesStep",
    "SshSetupStep",
    "UsersStep",
    "WelcomeStep",
    "WizardState",
    "WizardStep",
]
