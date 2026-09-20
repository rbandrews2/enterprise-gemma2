"""Pinned, visually checked table transcription. Never produces coordinates."""
from shared.placement_preview import PlacementPreviewRequest

REVISION = 'f16aa1782e85c4b1237823eb8fbaafdf06128f3cc8d2c17c16fb696b92415274'
URL = 'https://www.vdot.virginia.gov/media/vdotvirginiagov/doing-business/technical-guidance-and-support/traffic-operations/work-zones/vwapm-2026-01-28_acc.pdf'
BUFFER = {20:115, 25:155, 30:200, 35:250, 40:305, 45:360, 50:425, 55:495, 60:570, 65:645, 70:730, 75:820}


def preview(request: PlacementPreviewRequest):
    speed, road = request.posted_speed_mph, request.road_class
    spacing = None
    if road == 'limited_access':
        spacing = (1300, 1500)
    elif speed <= 35:
        # Limited-access roads are handled above; other classes are conventional roads.
        spacing = (100, 200)
    elif 40 <= speed <= 45:
        spacing = (350, 500)
    elif road == 'undivided' and 50 <= speed <= 55:
        spacing = (500, 800)
    elif road == 'divided_non_limited' and speed >= 50:
        spacing = (1000, 1300)
    buffer = BUFFER.get(speed)
    return {
        'rule_id': 'vdot-ttc4-reference-tables', 'rule_version': '1.0.0',
        'status': 'reference_only' if spacing and buffer is not None else 'unsupported_table_input',
        'inputs': request.model_dump(mode='json'),
        'advance_warning_spacing_ft': {'minimum':spacing[0], 'maximum':spacing[1],
            'classification':'recommended_range', 'table':'6P-V3'} if spacing else None,
        'buffer_space_ft': {'minimum':buffer, 'table':'6P-V4'} if buffer is not None else None,
        'citation': {'source_id':'vdot-vwapm-2026', 'revision':REVISION,
            'edition':'11.0 January 2026', 'pdf_page':157, 'printed_page':147,
            'url':URL+'#page=157', 'scenario_notes_pdf_page':166, 'scenario_figure_pdf_page':167,
            'review_status':'transcription_visually_checked_applicability_unreviewed',
            'checked_by':'Codex technical source review', 'checked_on':'2026-09-20'},
        'limitations': [
            'Pinned source snapshot; current amendments and project applicability must be checked.',
            'TTC-4.0 diagram is marked Known Error and has inconsistent note references. Resolve before using its sign layout.',
            'Spacing is a range, not a selected distance. No interpolation or extrapolation of buffer values is performed.',
            'This is not a complete TTC-4.0 plan: tapers, devices, vehicles, signs, intersections and field conditions require review.',
            'No flagger need or position is determined by this shoulder-work preview.',
        ],
        'placements': [], 'can_generate_placements':False, 'approved_for_field_use':False,
    }
