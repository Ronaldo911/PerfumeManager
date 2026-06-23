from utils.constants import DEFAULT_PIN, RESET_PIN

class SecurityController:
    @staticmethod
    def verify_pin(pin):
        return pin == DEFAULT_PIN

    @staticmethod
    def verify_reset_pin(pin):
        return pin == RESET_PIN
