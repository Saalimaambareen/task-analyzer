from django.test import TestCase
from .scoring import simple_score, smart_balance_score, detect_cycle
import datetime

class ScoringTests(TestCase):
    def test_simple_score_quick_high_importance(self):
        t = {'title':'A','due_date':None,'estimated_hours':1,'importance':9,'dependencies':[]}
        s = simple_score(t)
        self.assertTrue(s > 50)

    def test_smart_balance_priority_due_soon(self):
        today = datetime.date.today()
        due = (today + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        t = {'title':'DueSoon','due_date':due,'estimated_hours':5,'importance':5,'dependencies':[]}
        score, breakdown = smart_balance_score(t, {'DueSoon':t})
        self.assertTrue(score > 40)

    def test_detect_cycle(self):
        tasks = [
            {'title':'a','dependencies':['b']},
            {'title':'b','dependencies':['c']},
            {'title':'c','dependencies':['a']},
        ]
        cycles = detect_cycle(tasks)
        self.assertTrue(len(cycles) >= 1)
