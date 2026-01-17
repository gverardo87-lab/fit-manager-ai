# core/workflow_engine.py (Versione con Typo Corretto)
"""
Workflow Engine per CapoCantiere AI
Sistema professionale per la gestione delle fasi di lavoro navali
con dipendenze tra ruoli e calcolo strategico del fabbisogno di ore residue.
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import pandas as pd

class WorkRole(Enum):
    CARPENTIERE = "Carpentiere"  # <-- ERRORE CORRETTO QUI
    AIUTANTE_CARPENTIERE = "Aiutante Carpentiere"
    SALDATORE = "Saldatore"
    MOLATORE = "Molatore"
    CAPOCANTIERE = "Capocantiere"
    
    @classmethod
    def from_string(cls, role_str: str) -> Optional['WorkRole']:
        if not isinstance(role_str, str): return None
        role_str_upper = role_str.upper().replace(' ', '_')
        for role in cls:
            if role.name == role_str_upper: return role
        return None

@dataclass
class WorkPhase:
    role: WorkRole
    hours_required: float
    can_parallel: bool = False
    requires_roles: List[WorkRole] = field(default_factory=list)

@dataclass
class WorkflowTemplate:
    name: str
    activity_type: str
    phases: List[WorkPhase]
    description: str = ""
    
    def get_total_hours(self) -> float:
        """Calcola il monte ore totale standard (considera la durata, non la somma delle ore parallele)."""
        total_duration = 0
        parallel_phase_duration = 0
        for p in self.phases:
            if p.can_parallel:
                parallel_phase_duration = max(parallel_phase_duration, p.hours_required)
            else:
                total_duration += p.hours_required
        return total_duration + parallel_phase_duration

class NavalWorkflowEngine:
    def __init__(self):
        self.templates: Dict[str, WorkflowTemplate] = {}
        self._initialize_default_templates()
    
    def _initialize_default_templates(self):
        self.templates["MON"] = WorkflowTemplate(
            name="Montaggio Scafo", activity_type="MON",
            description="Workflow standard per il montaggio dello scafo basato su ore di lavoro per fase.",
            phases=[
                WorkPhase(role=WorkRole.CARPENTIERE, hours_required=80.0, can_parallel=True, requires_roles=[WorkRole.AIUTANTE_CARPENTIERE]),
                WorkPhase(role=WorkRole.AIUTANTE_CARPENTIERE, hours_required=80.0, can_parallel=True),
                WorkPhase(role=WorkRole.SALDATORE, hours_required=64.0, can_parallel=False),
                WorkPhase(role=WorkRole.MOLATORE, hours_required=40.0, can_parallel=False),
                WorkPhase(role=WorkRole.CAPOCANTIERE, hours_required=8.0, can_parallel=False)
            ]
        )
        self.templates["FAM"] = WorkflowTemplate(
            name="Fuori Apparato Motore", activity_type="FAM",
            description="Workflow standard per attività FAM, include collaudo.",
            phases=[
                WorkPhase(role=WorkRole.CARPENTIERE, hours_required=88.0, can_parallel=True, requires_roles=[WorkRole.AIUTANTE_CARPENTIERE]),
                WorkPhase(role=WorkRole.AIUTANTE_CARPENTIERE, hours_required=88.0, can_parallel=True),
                WorkPhase(role=WorkRole.SALDATORE, hours_required=72.0, can_parallel=False),
                WorkPhase(role=WorkRole.MOLATORE, hours_required=48.0, can_parallel=False),
                WorkPhase(role=WorkRole.CAPOCANTIERE, hours_required=16.0, can_parallel=False)
            ]
        )
    
    def get_workflow_for_activity(self, activity_id: str) -> Optional[WorkflowTemplate]:
        if not activity_id or '-' not in activity_id: return None
        prefix = activity_id.split('-')[0].upper()
        return self.templates.get(prefix)

    def calculate_remaining_hours_per_role(self, activity_id: str, hours_already_worked: float) -> Dict[WorkRole, float]:
        workflow = self.get_workflow_for_activity(activity_id)
        if not workflow: return {}

        remaining_hours: Dict[WorkRole, float] = {}
        accumulated_duration = 0.0
        
        # Gestione fasi parallele
        parallel_phase_duration = 0
        for p in workflow.phases:
            if p.can_parallel:
                parallel_phase_duration = max(parallel_phase_duration, p.hours_required)

        # Prima le fasi parallele, se esistono
        if parallel_phase_duration > 0:
            hours_covered = max(0, hours_already_worked - accumulated_duration)
            remaining_duration = max(0, parallel_phase_duration - hours_covered)
            if remaining_duration > 0:
                parallel_roles = [p.role for p in workflow.phases if p.can_parallel]
                for role in set(parallel_roles):
                    remaining_hours[role] = remaining_hours.get(role, 0) + remaining_duration
            accumulated_duration += parallel_phase_duration

        # Poi le fasi sequenziali
        for phase in workflow.phases:
            if not phase.can_parallel:
                hours_covered = max(0, hours_already_worked - accumulated_duration)
                remaining_duration = max(0, phase.hours_required - hours_covered)
                if remaining_duration > 0:
                    remaining_hours[phase.role] = remaining_hours.get(phase.role, 0) + remaining_duration
                accumulated_duration += phase.hours_required
        
        return remaining_hours

    def get_bottleneck_analysis(self, activities: List[Dict], available_workers: Dict[WorkRole, int], worked_hours: Dict[str, float]) -> Dict[str, Any]:
        demand = {role: 0.0 for role in WorkRole}
        for act in activities:
            act_id = act.get('id_attivita', '')
            wf = self.get_workflow_for_activity(act_id)
            if not wf or worked_hours.get(act_id, 0) >= wf.get_total_hours(): continue
            rem_hours = self.calculate_remaining_hours_per_role(act_id, worked_hours.get(act_id, 0))
            for role, hours in rem_hours.items():
                demand[role] += hours
        
        bottlenecks = []
        for role, demand_h in demand.items():
            if demand_h <= 0: continue
            workers = available_workers.get(role, 0)
            available_h = workers * 40
            if workers == 0:
                bottlenecks.append({'role': role.value, 'severity': 'CRITICO', 'demand_hours': demand_h, 'available_workers': 0, 'shortage_hours': demand_h})
            elif demand_h > available_h:
                bottlenecks.append({'role': role.value, 'severity': 'ALTO', 'demand_hours': demand_h, 'available_workers': workers, 'shortage_hours': demand_h - available_h})
        
        return {'bottlenecks': sorted(bottlenecks, key=lambda x: x['shortage_hours'], reverse=True), 'total_demand': {r.value: round(h) for r, h in demand.items() if h > 0}}

    def suggest_optimal_schedule(self, activities: List[Dict], workers: List[Dict], worked_hours: Dict[str, float]) -> List[Dict]:
        suggestions = []
        # Implementazione disabilitata per stabilità, da riattivare in futuro
        return suggestions

# Istanza globale
workflow_engine = NavalWorkflowEngine()


# ════════════════════════════════════════════════════════════════════════════════
# SEZIONE FITNESS & PERSONAL TRAINING (Integrazione Workout Generator)
# ════════════════════════════════════════════════════════════════════════════════

class FitnessWorkflowEngine:
    """
    Motore di workflow per il fitness e personal training.
    Gestisce:
    - Generazione piani di allenamento personalizzati
    - Periodizzazione macrocicli
    - Progressione e deload
    - Assessment e testing
    """
    
    def __init__(self):
        """Inizializza il fitness workflow engine."""
        try:
            from core.workout_generator import WorkoutGenerator
            self.workout_generator = WorkoutGenerator()
            self.initialized = True
        except Exception as e:
            import traceback
            # Logger solo in debug, non in console
            self.workout_generator = None
            self.initialized = False
            # Silenzioso: il motore funziona senza WorkoutGenerator per ora
    
    def generate_personalized_plan(
        self,
        client_profile: Dict[str, Any],
        weeks: int = 4,
        sessions_per_week: int = 3
    ) -> Dict[str, Any]:
        """
        Genera un piano di allenamento personalizzato basato su RAG.
        
        Args:
            client_profile: Profilo cliente con goal, livello, disponibilità
            weeks: Durata del programma
            sessions_per_week: Numero di sessioni per settimana
        
        Returns:
            Piano strutturato con esercizi, progressione, recovery
        """
        if not self.initialized or not self.workout_generator:
            return {'error': 'WorkoutGenerator non disponibile. Carica la knowledge base.'}
        
        return self.workout_generator.generate_workout_plan(
            client_profile,
            weeks=weeks,
            sessions_per_week=sessions_per_week
        )
    
    def create_macrocycle(
        self,
        goal: str,
        duration_weeks: int = 12,
        periodization_type: str = 'linear'
    ) -> Dict[str, Any]:
        """
        Crea un macrociclo di allenamento con periodizzazione.
        
        Args:
            goal: 'strength', 'hypertrophy', 'endurance', 'fat_loss'
            duration_weeks: Durata totale in settimane
            periodization_type: 'linear', 'block', 'undulating'
        
        Returns:
            Struttura macrociclo con fasi di allenamento
        """
        phases = {
            'linear': self._create_linear_periodization(goal, duration_weeks),
            'block': self._create_block_periodization(goal, duration_weeks),
            'undulating': self._create_undulating_periodization(goal, duration_weeks)
        }
        
        selected_phase = phases.get(periodization_type, phases['linear'])
        
        return {
            'goal': goal,
            'duration_weeks': duration_weeks,
            'periodization_type': periodization_type,
            'phases': selected_phase,
            'total_volume': self._calculate_total_volume(selected_phase),
            'intensity_progression': self._calculate_intensity_curve(goal, duration_weeks)
        }
    
    def _create_linear_periodization(self, goal: str, weeks: int) -> List[Dict[str, Any]]:
        """Periodizzazione lineare: aumenta intensità, diminuisce volume."""
        return [
            {'phase': 'Hypertrophy', 'weeks': weeks // 3, 'reps': '8-12', 'intensity': '70-80%'},
            {'phase': 'Strength', 'weeks': weeks // 3, 'reps': '3-6', 'intensity': '85-95%'},
            {'phase': 'Power', 'weeks': weeks // 3, 'reps': '1-3', 'intensity': '95%+'}
        ]
    
    def _create_block_periodization(self, goal: str, weeks: int) -> List[Dict[str, Any]]:
        """Periodizzazione a blocchi: concentra stimoli per adattamento specifico."""
        return [
            {'phase': 'Accumulation Block', 'weeks': weeks // 3, 'focus': 'Volume', 'intensity': '65-75%'},
            {'phase': 'Intensification Block', 'weeks': weeks // 3, 'focus': 'Intensity', 'intensity': '85-92%'},
            {'phase': 'Realization Block', 'weeks': weeks // 3, 'focus': 'Peak Performance', 'intensity': '90%+'}
        ]
    
    def _create_undulating_periodization(self, goal: str, weeks: int) -> List[Dict[str, Any]]:
        """Periodizzazione ondulante: varia volume e intensità settimanalmente."""
        return [
            {'week': f'Week {i}', 'focus': ['Hypertrophy', 'Strength', 'Power'][i % 3]}
            for i in range(1, weeks + 1)
        ]
    
    def _calculate_total_volume(self, phases: List[Dict]) -> int:
        """Calcola volume totale (somma di set * reps * peso)."""
        # Implementazione semplificata
        return sum(p.get('weeks', 1) * 100 for p in phases)
    
    def _calculate_intensity_curve(self, goal: str, weeks: int) -> List[float]:
        """Calcola la curva di intensità nel tempo."""
        base_intensity = {'strength': 0.85, 'hypertrophy': 0.75, 'endurance': 0.65, 'fat_loss': 0.70}
        intensity = base_intensity.get(goal, 0.75)
        
        return [intensity + (0.05 * (i / weeks)) for i in range(weeks)]
    
    def calculate_estimated_progress(
        self,
        client_profile: Dict[str, Any],
        duration_weeks: int
    ) -> Dict[str, Any]:
        """
        Stima il progresso atteso in base al profilo e durata.
        
        Returns:
            Previsioni realistiche di guadagni (forza, massa, perdita grasso)
        """
        level = client_profile.get('level', 'intermediate')
        goal = client_profile.get('goal', 'general')
        
        # Coefficienti per livello
        progression_coefficients = {
            'beginner': 1.5,
            'intermediate': 1.0,
            'advanced': 0.5
        }
        
        base_progress = {
            'strength': {'male': 15, 'female': 10},  # % aumento strength
            'hypertrophy': {'male': 5, 'female': 3},  # % aumento massa
            'fat_loss': {'male': 12, 'female': 10},  # % perdita grasso
            'endurance': {'male': 20, 'female': 18}  # % miglioramento VO2
        }
        
        coefficient = progression_coefficients.get(level, 1.0)
        base = base_progress.get(goal, {})
        
        return {
            'estimated_progress': {
                k: v * coefficient * (duration_weeks / 12) 
                for k, v in base.items()
            },
            'confidence': 'Alta' if level in ['beginner', 'intermediate'] else 'Media',
            'recommendations': [
                'Mantieni consistenza negli allenamenti',
                'Monitora progressivamente il carico',
                'Registra i dati di performance settimanalmente',
                'Adatta la nutrizione all\'obiettivo'
            ]
        }

# Istanza globale fitness
fitness_workflow = FitnessWorkflowEngine()


def get_workflow_info(activity_id: str) -> Dict[str, Any]:
    workflow = workflow_engine.get_workflow_for_activity(activity_id)
    if not workflow: return {'error': f'Nessun workflow trovato per {activity_id}'}
    return {
        'name': workflow.name, 'type': workflow.activity_type, 'description': workflow.description,
        'total_hours': workflow.get_total_hours(),
        'phases': [{'role': p.role.value, 'hours': p.hours_required, 'parallel': p.can_parallel, 'requires': [r.value for r in p.requires_roles]} for p in workflow.phases]
    }

def analyze_resource_allocation(presence_data: List[Dict], schedule_data: List[Dict]) -> Dict[str, Any]:
    if not presence_data or not schedule_data: return {'error': 'Dati mancanti.'}
    df_presence = pd.DataFrame(presence_data)
    worked_hours = df_presence.groupby('id_attivita')['ore_lavorate'].sum().to_dict()
    unique_workers = {(r.get('operaio'), r.get('ruolo')) for r in presence_data if r.get('operaio')}
    workers_count = {}
    for _, role_str in unique_workers:
        role = WorkRole.from_string(role_str)
        if role: workers_count[role] = workers_count.get(role, 0) + 1
    
    analysis = workflow_engine.get_bottleneck_analysis(schedule_data, workers_count, worked_hours)
    suggestions = workflow_engine.suggest_optimal_schedule(schedule_data, presence_data, worked_hours)
    
    return {
        'workers_by_role': {r.value: c for r, c in workers_count.items()},
        'bottleneck_analysis': analysis,
        'schedule_suggestions': suggestions
    }