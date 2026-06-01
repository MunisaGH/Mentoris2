from allauth.account.adapter import DefaultAccountAdapter

class NoSignupAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        """
        Ochiq ro'yxatdan o'tishni butunlay yopish.
        Faqat admin tomondan "Super Login/Parol" berilganlar kira oladi.
        """
        return False
