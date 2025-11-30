from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import TaskSerializer
from .scoring import simple_score, smart_balance_score, detect_cycle, parse_date
from datetime import date

class AnalyzeTasksView(APIView):
    def post(self, request):
        tasks_data = request.data.get('tasks') or request.data
        if not isinstance(tasks_data, list):
            return Response({'error':'Expecting a JSON array of tasks or {tasks: [...]}.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = TaskSerializer(data=tasks_data, many=True)
        if not serializer.is_valid():
            return Response({'error':'Validation failed', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        tasks = serializer.validated_data

        tasks_index = {}
        for t in tasks:
            tid = t.get('id') or t.get('title')
            tasks_index[tid] = t

        cycles = detect_cycle(tasks)
        strategy = request.query_params.get('strategy', 'smart').lower()

        results = []
        for t in tasks:
            tid = t.get('id') or t.get('title')
            if strategy == 'simple':
                score = simple_score(t)
                breakdown = {'method':'simple'}
            elif strategy == 'fastest':
                score = round((1.0 / (t.get('estimated_hours',1.0)+0.1)) * 80 + (t.get('importance',5) * 2),2)
                breakdown = {'method':'fastest'}
            elif strategy == 'impact':
                score = round((t.get('importance',5)/10.0) * 100,2)
                breakdown = {'method':'impact'}
            elif strategy == 'deadline':
                due_date = parse_date(t.get('due_date'))
                if due_date is None:
                    score = 40.0
                else:
                    days = (due_date - date.today()).days
                    if days < 0:
                        score = 100.0
                    else:
                        score = round(max(0, 100 - days), 2)
                breakdown = {'method':'deadline'}
            else:
                score, breakdown = smart_balance_score(t, tasks_index)

            results.append({'task':t, 'score': score, 'breakdown': breakdown})

        results_sorted = sorted(results, key=lambda r: r['score'], reverse=True)
        out = {'strategy': strategy, 'cycles': cycles, 'results': results_sorted}
        return Response(out, status=status.HTTP_200_OK)


class SuggestTasksView(APIView):
    def post(self, request):
        tasks = request.data.get('tasks') or request.data
        if not isinstance(tasks, list):
            return Response({'error':'Please provide tasks as JSON array in body as {tasks: [...]}'}, status=status.HTTP_400_BAD_REQUEST)

        strategy = request.query_params.get('strategy', 'smart').lower()
        tasks_index = {}
        for t in tasks:
            tid = t.get('id') or t.get('title')
            tasks_index[tid] = t

        cycles = detect_cycle(tasks)
        scored = []
        for t in tasks:
            if strategy == 'simple':
                score = simple_score(t)
            else:
                score, breakdown = smart_balance_score(t, tasks_index)
            explanation = []
            explanation.append(f"Importance: {t.get('importance',5)}")
            if t.get('due_date'):
                pd = parse_date(t.get('due_date'))
                if pd:
                    explanation.append(f"Due in {(pd - date.today()).days} days")
            explanation.append(f"Estimated hours: {t.get('estimated_hours',1.0)}")
            if t.get('dependencies'):
                explanation.append(f"Depends on {len(t.get('dependencies'))} tasks")
            scored.append({'task':t,'score':score,'explanation':'. '.join(explanation)})

        scored_sorted = sorted(scored, key=lambda x: x['score'], reverse=True)
        top3 = scored_sorted[:3]
        for item in top3:
            reasons = []
            t = item['task']
            if t.get('due_date'):
                du = (parse_date(t.get('due_date')) - date.today()).days
                if du < 0:
                    reasons.append('Past due — needs immediate attention')
                elif du <= 2:
                    reasons.append('Due very soon')
            if t.get('importance',5) >= 8:
                reasons.append('High importance')
            if t.get('estimated_hours',1.0) <= 2:
                reasons.append('Quick win')
            if t.get('dependencies'):
                reasons.append('Blocks other tasks')
            item['why'] = reasons or ['Balanced priority (no single dominating factor)']

        return Response({'strategy': strategy, 'cycles': cycles, 'suggestions': top3}, status=200)
