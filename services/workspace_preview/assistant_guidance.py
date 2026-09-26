"""Verified product help and saved-state answers; never model-generated advice.

Narrow routing covers known application facts. Project-specific planning and
ambiguous/free-form questions continue through the model path.
"""
import re
from dataclasses import dataclass
from services.workspace_preview.intelligence import module_context


@dataclass(frozen=True)
class Guidance:
    answer: str
    topic: str
    target: str | None


def workspace_guidance(payload, context):
    question = ' '.join(payload.question.casefold().split())
    # Do not summarize a long project description with a generic help paragraph.
    if len(question) > 400:
        return None
    if re.search(r'\b(am i clocked (?:in|out)|am i on break|current clock status)\b', question):
        clock = context.get('time_clock')
        if not clock:
            return Guidance('Open Time clock to check your saved status.', 'clock_status', 'time_clock')
        labels = {'working':'clocked in and working', 'on_break':'clocked in and on a break', 'off_clock':'off the clock'}
        status = labels.get(clock['status'], 'in an unknown recorded state')
        return Guidance(f"Your saved time-clock record shows you are {status}, as of {clock['as_of']}. "
                        'Atlas has not changed your attendance. Use Time clock to record any change.', 'clock_status', 'time_clock')
    if re.search(r'\bchecklist\b', question) and re.search(r'\b(current|stale|latest|version|saved)\b', question):
        job = context.get('saved_job')
        checklist = context.get('readiness_checklist') or {}
        if not job:
            return Guidance('Select a saved work order first so I can check its saved checklist revision.', 'checklist_status', 'job_board')
        prefix = f"Saved job: {job['title']} (revision {job['version']}). "
        if checklist.get('status') != 'saved':
            answer = 'No readiness checklist is saved for this job. This does not mean the work was not done.'
        elif checklist.get('stale'):
            answer = (f"Checklist revision {checklist['version']} belongs to job revision {checklist['order_version']}. "
                      'The job has changed: review every checklist category and save a new revision. The checklist is not current.')
        else:
            answer = (f"Checklist revision {checklist['version']} matches this saved job revision. "
                      'That only confirms the version match; it does not verify field conditions, source freshness or agency approval.')
        return Guidance(prefix + answer, 'checklist_status', 'checklist')

    # A known unavailable app capability, not an answer about real-world placement.
    if re.search(r'\b(can you|can atlas|can wzos)\b', question) and re.search(r'\b(flagger positions?|sign placement|placement coordinates)\b', question):
        return Guidance('Atlas cannot generate approved sign or flagger positions in this workspace. '
                        'Placement recommendations need measured site geometry, verified governing documents and qualified review. '
                        'Work Zone Report is an Enterprise draft workflow; a draft is not field approval.', 'placement_capability',
                        'report' if context['edition'] == 'enterprise' else None)

    # Regulatory and project requirements must not be answered with an app guide.
    if re.search(r'\b(vdot|mutcd|osha|vosh|law|permit|mandatory|required|compliant|compliance|feet|mph)\b', question):
        return None
    cue = re.search(r'\b(how|where|can|does|do|is|will|what|which|show|help)\b', question)
    if not cue:
        return None
    rules = [
        ('training', r'\b(certificate|certification|study status)\b', r'\b(issue|grant|earn|certif\w*|complete|completion|status)\b'),
        ('schedule', r'\b(schedule|scheduling)\b', r'\b(assign|edit|create|member|admin|crew)\b'),
        ('time_clock', r'\b(clock|time clock|break|shift)\b', r'\b(clock|start|end|record|switch|in|out)\b'),
        ('messages', r'\b(sms|mms|text message|messages?|email)\b', r'\b(send|deliver|message|inbox)\b'),
        ('forms', r'\b(vehicle|inspection|defects?)\b', r'\b(record|save|saving|clear|defects?|inspection)\b'),
        ('work_orders', r'\bwork orders?\b', r'\b(save|create|edit|new)\b'),
        ('navigation', r'\b(directions|navigation|google maps)\b', r'\b(open|use|find|saved|job)\b'),
    ]
    matches = [module for module, topic, action in rules if re.search(topic, question) and re.search(action, question)]
    # Multi-module requests need a conversational response, not a partial answer.
    if len(matches) != 1:
        return None
    module = matches[0]
    answer = module_context(module, context['role'])['guidance']
    if module == 'training':
        answer = 'Changing study status does not issue a certificate or certify course completion. ' + answer
    elif module == 'messages':
        answer = 'Atlas cannot send a text, MMS or email from this workspace. ' + answer
    elif module == 'time_clock':
        answer = 'Atlas cannot clock you in or change attendance. ' + answer
    return Guidance(answer, module, {'work_orders':'job_board'}.get(module, module))
