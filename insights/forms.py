from django import forms
from django.utils import timezone

from chat.models import ChatBot


class StatsForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        if not self.user.is_superuser:
            self.fields["bots"].queryset = ChatBot.objects.filter(
                group__in=self.user.groups.all()
            )

    bots = forms.ModelMultipleChoiceField(
        queryset=ChatBot.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Bots",
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Startdatum",
    )
    end_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"}), label="Enddatum"
    )

    group_by = forms.ChoiceField(
        choices=(
            ("day", "Tag"),
            ("week", "Woche"),
            ("month", "Monat"),
            ("year", "Jahr"),
        ),
        initial="day",
        label="Gruppieren nach",
    )

    def clean(self):
        # Check if start_date is before end_date
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Startdatum muss vor dem Enddatum liegen.")
        return cleaned_data
