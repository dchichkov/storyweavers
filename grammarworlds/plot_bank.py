"""Authored narrative readings, grounded in the existing twenty source worlds.

Archetypes are partial analogies, not calibrated classifications or claims that
these miniature stories instantiate every stage of Booker's larger plots.
"""
from .event_scale_bank import BANK as SCALES

ARCHETYPES = ('overcoming_the_monster','rags_to_riches','quest','voyage_and_return',
              'comedy','tragedy','rebirth','mystery','rebellion')
ROLE_STAGE = {
    'desire':'setup','lack':'setup','promise':'setup',
    'setback':'complication','failed_attempt':'complication','threat':'complication','conflict':'complication',
    'clue':'development','discovery':'development','choice':'development','revision':'development',
    'help':'development','attempt':'development',
    'decisive_action':'resolution','payoff':'resolution','final_image':'aftermath',
    'supporting_action':'support',
}


def reading(pattern,archetypes,roles,stakes,why,events,links):
    assigned={}
    for role,kinds in events.items():
        for kind in kinds.split():
            if kind in assigned:raise ValueError('duplicate narrative role: '+kind)
            assigned[kind]=dict(role=role,stage=ROLE_STAGE[role],basis='authored_event_reading')
    return dict(local_pattern=pattern,archetypes=[dict(name=a,fit='partial',basis='authored_interpretation') for a in archetypes.split()],
        roles={k:v.split() for k,v in roles.items()},stakes=stakes,rationale=why,events=assigned,
        links=[dict(source=a,target=b,relation=c) for a,b,c in links])


BANK = {
'bakery':reading('imperfect_gift_accepted','quest',
 dict(protagonist='hero',helper='helper',recipient='recipient',central_object='cake'),
 'A lonely recipient may miss birthday company.', 'A small delivery quest; acceptance matters more than a perfect cake.',
 dict(desire='birthday_request',setback='bumped_icing',choice='paved_route wait_for_cart',payoff='cake_arrives imperfect_gift birthday_light',final_image='bright_window'),
 [('birthday_request','imperfect_gift','payoff_of'),('bumped_icing','imperfect_gift','reframes'),('birthday_light','bright_window','ending_evidence')]),
'puppets':reading('loss_replacement_contribution','quest',
 dict(protagonist='hero',helper='helper',central_object='star',missing_object='old_star'),
 'The performance lacks its star prop.', 'A missing-prop task with a confidence turn; not a full performance narrative.',
 dict(lack='missing_prop',choice='make_replacement',attempt='sew_button',revision='shorten_loop double_loop',decisive_action='speak_up offer_star',final_image='last_light'),
 [('missing_prop','make_replacement','responds_to'),('sew_button','shorten_loop double_loop','refines'),('missing_prop','offer_star','payoff_of'),('offer_star','last_light','ending_evidence')]),
'greenhouse':reading('competing_needs_care_with_consequences','',
 dict(protagonist='hero',helper='caretaker owner',central_object='tomatoes sunflower',resource='barrel tap'),
 'Limited water and broken shade endanger the plants.', 'A resource allocation dilemma; no strong fit to a complete nine-plot archetype.',
 dict(conflict='notice',choice='choose_seedlings choose_flower choose_share',attempt='water_first',setback='shade_break',revision='secure move_flower',help='repair_tap repair_shade',payoff='water_second',promise='promise_repair',final_image='ending'),
 [('notice','choose_seedlings choose_flower choose_share','responds_to'),('shade_break','secure move_flower','responds_to'),('repair_tap','water_second','enables'),('water_first','ending','consequence_revisited')]),
'seaside':reading('unsafe_route_corrected','quest',
 dict(protagonist='hero',helper='helper',central_object='book',guide='map',obstacle='tide'),
 'The rising tide threatens a safe place to draw.', 'A route-finding quest; no narrated return home, so not marked voyage-and-return.',
 dict(desire='windy_pages',failed_attempt='wrong_landmark',threat='rising_water',discovery='milo_reads_map tessa_checks_map',decisive_action='safe_steps',payoff='sheltered_sketch',final_image='pool_flower'),
 [('wrong_landmark','rising_water','escalates'),('rising_water','milo_reads_map tessa_checks_map','responds_to'),('milo_reads_map tessa_checks_map','safe_steps','uses_discovery'),('windy_pages','sheltered_sketch','payoff_of')]),
'library':reading('search_help_and_reciprocity','quest mystery',
 dict(protagonist='hero',helper='helper',beneficiary='friend',central_object='book atlas',clue_object='bookmark'),
 'A missing book competes with the protagonist’s own drawing plan.', 'A recovery quest with a small location mystery, not a full detective plot.',
 dict(desire='wish',lack='missing',failed_attempt='failed_search',clue='clue',choice='request_help reserve_atlas release_atlas',decisive_action='retrieve recognize checkout',help='share_picture share_atlas',payoff='sketch_whale sketch_moon',final_image='ending'),
 [('missing','failed_search','responds_to'),('clue','retrieve','uses_discovery'),('missing','checkout','payoff_of'),('wish','sketch_whale sketch_moon','payoff_of'),('checkout','share_picture share_atlas','reciprocity')]),
'snow':reading('temptation_help_delivery','quest',
 dict(protagonist='hero',helper='helper',recipient='recipient',central_object='basket',transport='sled'),
 'Groceries need delivering while the helper wants to race.', 'A delivery quest with a choice between racing and helping.',
 dict(promise='delivery_promise',setback='ice_ridge',choice='leave_race',decisive_action='lift_runner rock_runner clear_gate',payoff='deliver_food',final_image='warm_stove'),
 [('ice_ridge','leave_race','responds_to'),('leave_race','lift_runner rock_runner','enables'),('delivery_promise','deliver_food','payoff_of'),('deliver_food','warm_stove','ending_evidence')]),
'picnic':reading('welcome_despite_disruption','',
 dict(protagonist='hero',helper='helper',recipient='guest',central_object='basket blanket sandwich'),
 'The lunch must survive a gust and leave a portion for a late guest.', 'A care-and-welcome story without a strong full-archetype match.',
 dict(desire='welcome_plan',threat='gust',decisive_action='save_lunch secure_blanket',choice='save_portion',payoff='late_guest share_sandwich share_cookie',final_image='fold_together'),
 [('gust','save_lunch secure_blanket','responds_to'),('welcome_plan','save_portion','goal_progress'),('save_portion','share_sandwich share_cookie','payoff_of'),('welcome_plan','fold_together','ending_evidence')]),
'music':reading('respect_boundary_change_collaboration','',
 dict(protagonist='hero',partner='partner',audience='teacher',central_object='drum paper'),
 'A desired duet conflicts with the partner’s reluctance to perform publicly.', 'A negotiation of boundaries; insufficient evidence for a full rebirth or comedy arc.',
 dict(desire='opening invite',conflict='decline',choice='choose_solo offer_pattern offer_private',help='write_pattern',attempt='prepare_solo prepare_pattern',decisive_action='perform join',payoff='response',final_image='ending'),
 [('invite','decline','complicates'),('decline','choose_solo offer_pattern offer_private','responds_to'),('write_pattern','prepare_pattern','enables'),('opening','perform','revises_original_goal'),('response','ending','ending_evidence')]),
'market':reading('mistake_diagnosis_honest_repair','mystery',
 dict(protagonist='hero',helper='helper',recipient='customer',central_object='bag',instrument='scale',clue_object='leaf'),
 'A customer may receive an underweight order.', 'A local diagnostic mystery followed by honest correction.',
 dict(desire='order_goal',failed_attempt='weigh_order',discovery='discover_leaf',choice='admit_error',revision='mina_clears_leaf farah_clears_leaf',decisive_action='correct_weight',payoff='deliver_order',final_image='steady_dial'),
 [('weigh_order','discover_leaf','explains_problem'),('discover_leaf','admit_error','responds_to'),('discover_leaf','correct_weight','uses_discovery'),('order_goal','deliver_order','payoff_of'),('correct_weight','steady_dial','ending_evidence')]),
'camp':reading('search_without_abandoning_friend','quest mystery',
 dict(protagonist='hero',beneficiary='helper',central_object='rabbit',resource='lantern',clue_object='bell collar'),
 'A missing toy and a frightened friend must both be cared for.', 'A recovery quest with clues; friendship constrains how the search is conducted.',
 dict(lack='missing_rabbit',threat='dark_fork',clue='bell_clue collar_clue',choice='share_light',decisive_action='reach_from_path',payoff='return_rabbit',final_image='friendly_shadows'),
 [('dark_fork','share_light','responds_to'),('bell_clue collar_clue','reach_from_path','uses_discovery'),('missing_rabbit','return_rabbit','payoff_of'),('share_light','friendly_shadows','ending_evidence')]),
'pottery':reading('failed_attempt_user_led_redesign','quest',
 dict(protagonist='hero',helper='helper',recipient='grandpa',central_object='cup',instrument='tool'),
 'The gift must be usable by its recipient’s stiff hands.', 'A making-and-giving quest whose solution changes through consultation.',
 dict(lack='need',desire='goal',attempt='shape',setback='slip',discovery='inspect consult',revision='thumb smooth remake',decisive_action='fire',payoff='give use',final_image='ending'),
 [('slip','inspect consult','responds_to'),('consult','thumb smooth remake','uses_discovery'),('goal','give','payoff_of'),('need','use','payoff_of'),('use','ending','ending_evidence')]),
'orchard':reading('restrain_harm_choose_alternative','quest',
 dict(protagonist='hero',helper='helper',recipient='recipient',central_object='pear gift',threatened_object='branch'),
 'Obtaining fruit risks damaging the tree.', 'A small gift quest resolved by restraint and an alternative fruit.',
 dict(promise='pear_promise',failed_attempt='resisting_fruit',choice='protect_branch',revision='tessa_picks_low jun_steadies_picker trim_bruise',payoff='deliver_gift',final_image='unbent_branch'),
 [('resisting_fruit','protect_branch','responds_to'),('protect_branch','tessa_picks_low jun_steadies_picker','changes_strategy'),('pear_promise','deliver_gift','payoff_of'),('protect_branch','unbent_branch','ending_evidence')]),
'costume':reading('competing_wants_shared_solution','comedy',
 dict(protagonist='hero',partner='helper',central_object='cape disk ribbons'),
 'Both children want to take part with limited costumes.', 'A partial social-reconciliation pattern; comic misunderstandings are not required by this source.',
 dict(desire='wind_wish',conflict='wrong_costume',choice='share_cape',setback='dragging_hem',revision='gather_front lift_hem',help='give_sun',payoff='perform_together',final_image='return_costume'),
 [('wrong_costume','share_cape','responds_to'),('dragging_hem','gather_front lift_hem','responds_to'),('give_sun','perform_together','enables'),('wind_wish','perform_together','revises_original_goal')]),
'pond':reading('recovery_without_damaging_tool','quest',
 dict(protagonist='hero',beneficiary='helper',central_object='boat',instrument='net',obstacle='branch'),
 'Recovering the boat could damage the borrowed net.', 'A recovery quest resolved through a gentler approach.',
 dict(lack='drifting_boat',setback='net_snag',choice='refuse_yank',revision='turn_hoop ease_hoop',attempt='follow_path',decisive_action='net_boat',payoff='tether_boat',final_image='safe_circle'),
 [('net_snag','refuse_yank','responds_to'),('refuse_yank','turn_hoop ease_hoop','changes_strategy'),('drifting_boat','net_boat','payoff_of'),('tether_boat','safe_circle','ending_evidence')]),
'repair':reading('failed_attempt_diagnosis_changed_approach','mystery',
 dict(protagonist='hero',helper='helper mentor',central_object='cart wheel',beneficiary_object='plants',clue_object='string',instrument='spanner'),
 'A broken cart prevents moving the plant load.', 'A local diagnostic mystery: an unsuccessful repair leads to finding the obstruction.',
 dict(desire='cart_goal',failed_attempt='tighten_wrongly',choice='admit_and_shelter',discovery='diagnose_string',help='niko_holds_wheel rafi_holds_wheel',decisive_action='refit_and_test',payoff='move_plants',final_image='quiet_wheel'),
 [('tighten_wrongly','admit_and_shelter','responds_to'),('tighten_wrongly','diagnose_string','explains_problem'),('diagnose_string','refit_and_test','uses_discovery'),('cart_goal','move_plants','payoff_of'),('refit_and_test','quiet_wheel','ending_evidence')]),
'museum':reading('failed_experiment_controlled_retry','mystery',
 dict(protagonist='hero',helper='helper',recipient='visitor',central_object='shadow moth',instrument='torch',clue_object='label'),
 'The demonstration fails to produce the intended small shadow.', 'A local explanatory mystery resolved by controlling one variable.',
 dict(desire='exhibit_goal',failed_attempt='moving_light',discovery='read_small_print',revision='books_support clay_support',decisive_action='controlled_trial',payoff='visitor_turn',final_image='little_wings'),
 [('moving_light','read_small_print','responds_to'),('read_small_print','books_support clay_support','uses_discovery'),('books_support clay_support','controlled_trial','enables'),('exhibit_goal','little_wings','payoff_of')]),
'laundry':reading('ask_for_help_protect_shared_work','',
 dict(protagonist='hero',helper='helper',recipient='owner',central_object='sheet sock',instrument='bag'),
 'Clean washing risks falling when its support slips.', 'A cooperative domestic repair, without a strong full-archetype match.',
 dict(desire='help_washing',setback='slipping_prop',choice='ask_help',revision='move_inside fold_sheet drape_sheet',help='catch_sock',payoff='hang_sock',final_image='sheltered_sock'),
 [('slipping_prop','ask_help','responds_to'),('ask_help','move_inside','changes_strategy'),('help_washing','sheltered_sock','payoff_of')]),
'trail':reading('inclusive_route_and_shared_goals','quest',
 dict(protagonist='hero',partner='helper leni',central_object='book card',guide='map compass',obstacle='tree'),
 'A blocked route could exclude the child using crutches.', 'An inclusive outing quest; the source does not establish a full voyage-and-return arc.',
 dict(desire='three_wishes',choice='choose_loop',setback='blocked_trail',clue='align_map leni_spots_marker felix_clears_ivy',decisive_action='level_detour',payoff='salamander_sketch stamp_card',final_image='show_drawing'),
 [('blocked_trail','align_map','responds_to'),('align_map leni_spots_marker felix_clears_ivy','level_detour','uses_discovery'),('three_wishes','salamander_sketch stamp_card','payoff_of'),('level_detour','show_drawing','ending_evidence')]),
'festival':reading('notice_exclusion_redesign_access','',
 dict(protagonist='hero',partner='helper',central_object='flags moon string',threatened_object='gate cart'),
 'Decorations could block access and prevent shared participation.', 'An accessibility redesign with a demonstrated result; no strong full-archetype match.',
 dict(desire='reachable_bunting',failed_attempt='blocked_gate',choice='rethink_access',revision='move_to_fence double_wrap adjust_tension',payoff='tie_moon hang_flags',final_image='clear_passage'),
 [('blocked_gate','rethink_access','responds_to'),('rethink_access','move_to_fence','changes_strategy'),('reachable_bunting','tie_moon','payoff_of'),('blocked_gate','clear_passage','ending_evidence')]),
'biscuit':reading('conflict_shared_design_gift','comedy',
 dict(protagonist='hero',partner='helper',recipient='recipient',central_object='dough biscuit'),
 'Competing designs threaten the last dough and the thank-you gift.', 'A partial reconciliation pattern; a conflict is resolved by combining both contributions.',
 dict(desire='thank_you_gift',conflict='torn_dough',choice='repair_dough',decisive_action='cut_together',help='toby_marks_star mara_marks_star',payoff='pack_gift',final_image='sugar_star'),
 [('torn_dough','repair_dough','responds_to'),('repair_dough','cut_together','changes_strategy'),('thank_you_gift','pack_gift','payoff_of'),('toby_marks_star mara_marks_star','sugar_star','ending_evidence')]),
}

# Every native event has a role; unmarked logistics stay explicitly neutral.
for scenario,spec in BANK.items():
    spec['goal']=SCALES[scenario]['goal']
    for ep in SCALES[scenario]['episodes']:
        for kind in ep['events']:
            spec['events'].setdefault(kind,dict(role='supporting_action',stage='support',basis='neutral_default'))
