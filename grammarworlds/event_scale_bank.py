"""Authored coarse readings of the twenty intact seed stories.

Three meaningful episodes per story; fine events remain the executable source.
Duration bands are estimates, not measurements of human activity.
"""

def episode(name,events,ends,*,offers=(),duration=None):
    return dict(name=name,events=events.split(),ends=ends.split(),offers=list(offers),
                duration=duration or {'minute':.85,'hour':.15})


def story(goal,episodes,checks,*,tags):
    return dict(goal=goal,episodes=episodes,checks=checks,tags=tags.split(),
                duration={'hour':.9,'day':.1},persistence='until_achieved_or_abandoned')


def state(entity,value):return dict(kind='state',entity=entity,value=value)
def flag(value):return dict(kind='flag',value=value)

BANK={
'bakery':story('Bring a birthday gift and company',[
 episode('Prepare a protected delivery','birthday_request basket_permission borrow_basket','borrow_basket'),
 episode('Get the cake safely to its recipient','paved_route wait_for_cart bumped_icing cake_arrives','cake_arrives'),
 episode('Share the imperfect birthday gift','imperfect_gift birthday_light return_basket bright_window','bright_window',offers=('welcome','gift'))],
 [state('window','open'),state('cake','whole')],tags='care gift welcome delivery'),
'puppets':story('Help the puppet performance succeed',[
 episode('Replace the missing stage prop','missing_prop make_replacement fetch_needle','fetch_needle'),
 episode('Make the replacement safe to use','sew_button shorten_loop double_loop','shorten_loop double_loop'),
 episode('Speak up and contribute the star','speak_up offer_star return_needle last_light','last_light',offers=('performance','collaboration'))],
 [state('star','secure'),state('curtain','closed')],tags='performance confidence collaboration'),
'greenhouse':story('Care for both plants with limited water',[
 episode('Allocate the remaining water','notice borrow fill choose_seedlings choose_flower choose_share water_first','water_first'),
 episode('Restore water and temporary protection','shade_break secure move_flower repair_tap refill water_second','water_second',offers=('plant_care','water_supply')),
 episode('Restore the shade and future care','repair_shade promise_repair return ending','ending',offers=('plant_care','repair'))],
 [state('tomatoes','watered'),state('sunflower','watered')],tags='care plants water repair'),
'seaside':story('Draw the sea while staying safe',[
 episode('Locate a place to draw','windy_pages fetch_map wrong_landmark','wrong_landmark'),
 episode('Correct the route before the tide rises','rising_water milo_reads_map tessa_checks_map safe_steps','safe_steps',offers=('safe_route',)),
 episode('Draw from shelter','sheltered_sketch pool_flower','pool_flower',offers=('artwork',))],
 [state('book','sea_drawing'),state('hero','safe_route')],tags='artwork route safety'),
'library':story('Help recover a book while adapting a drawing plan',[
 episode('Search together for the missing book','wish missing borrow place_atlas failed_search clue request_help','request_help'),
 episode('Recover and lend the book','reserve_atlas release_atlas fetch_ladder retrieve recognize checkout checkout_atlas return_trolley return_ladder','checkout'),
 episode('Make and share the drawing','share_picture sketch_whale share_atlas sketch_moon ending','ending',offers=('artwork','collaboration'))],
 [state('book','checked_out'),flag('drawing_done')],tags='help artwork search collaboration'),
'snow':story('Deliver groceries instead of winning a race',[
 episode('Start the promised delivery','delivery_promise borrow_sled ice_ridge','ice_ridge'),
 episode('Free the sled together','leave_race lift_runner rock_runner clear_gate','clear_gate',offers=('transport_ready',)),
 episode('Bring the food inside','deliver_food return_sled warm_stove','warm_stove',offers=('delivery','care'))],
 [state('stove','warm'),state('sled','free')],tags='delivery transport help'),
'picnic':story('Welcome a late friend and preserve the picnic',[
 episode('Prepare a welcome','welcome_plan borrow_blanket gust','gust'),
 episode('Save the lunch and reserve a portion','save_lunch fetch_weight secure_blanket save_portion','save_portion',offers=('food_ready',)),
 episode('Share the picnic with the late guest','late_guest share_sandwich share_cookie fold_together','fold_together',offers=('welcome','shared_food'))],
 [state('basket','safe'),state('guest','arrived'),state('blanket','folded')],tags='welcome food care'),
'music':story('Make music while respecting a partner’s boundary',[
 episode('Discover the partner’s boundary','opening borrow invite decline','decline'),
 episode('Agree on a workable performance','choose_solo offer_pattern offer_private write_pattern prepare_solo prepare_pattern pickup','prepare_solo prepare_pattern pickup'),
 episode('Perform and acknowledge the collaboration','perform join response return ending','ending',offers=('performance','collaboration'))],
 [flag('performed'),state('hero','accepted_boundary')],tags='performance collaboration consent'),
'market':story('Correct a weighing mistake and deliver a fair order',[
 episode('Weigh the order','order_goal borrow_scale weigh_order','weigh_order'),
 episode('Find and correct the biased scale','discover_leaf admit_error mina_clears_leaf farah_clears_leaf correct_weight','correct_weight',offers=('measurement','repair')),
 episode('Deliver the corrected order','deliver_order return_scale steady_dial','steady_dial',offers=('delivery',))],
 [state('bag','correct_weight'),state('scale','zeroed')],tags='honesty measurement delivery'),
'camp':story('Find the rabbit without leaving a frightened friend',[
 episode('Begin the search together','missing_rabbit borrow_lantern dark_fork','dark_fork'),
 episode('Find the rabbit while sharing the light','bell_clue collar_clue share_light reach_from_path','reach_from_path',offers=('recovery','collaboration')),
 episode('Return the rabbit and lantern','return_rabbit return_light friendly_shadows','friendly_shadows',offers=('care',))],
 [state('rabbit','free'),state('hero','stays_together')],tags='care recovery collaboration'),
'pottery':story('Make a useful cup for Grandpa’s hand',[
 episode('Understand the damaged cup and its intended user','need goal shape slip inspect consult fetch_sponge','consult'),
 episode('Adapt the grip and shape','thumb smooth remake return_rib return_sponge shelve','shelve',offers=('accessible_design',)),
 episode('Dry fire cool and deliver a usable cup','dry load_bisque bisque cool_bisque unload_bisque glaze load_final fire cool_final deliver give use ending','ending',offers=('gift','craft'),duration={'hour':.2,'day':.8})],
 [state('cup','cool'),state('cup','fired')],tags='gift craft accessibility patience'),
'orchard':story('Give a ripe pear without harming the tree',[
 episode('Try to collect the promised pear','pear_promise borrow_picker resisting_fruit','resisting_fruit'),
 episode('Choose ripe fruit and protect the branch','protect_branch tessa_picks_low jun_steadies_picker trim_bruise','trim_bruise',offers=('food_ready',)),
 episode('Deliver the gift and return the tool','return_picker deliver_gift unbent_branch','unbent_branch',offers=('gift','delivery'))],
 [state('pear','trimmed'),state('branch','unbent')],tags='gift care food'),
'costume':story('Share costumes so both children can perform',[
 episode('Notice the missing costume','wind_wish borrow_cape wrong_costume','wrong_costume'),
 episode('Adapt and share the available props','share_cape dragging_hem gather_front lift_hem fetch_sun give_sun','give_sun',offers=('accessible_design','collaboration')),
 episode('Perform together and return the costume','perform_together return_costume','return_costume',offers=('performance',))],
 [state('hero','performed'),state('helper','performed'),state('cape','intact')],tags='performance collaboration costume'),
'pond':story('Recover the boat without breaking the borrowed net',[
 episode('Try to reach the drifting boat','drifting_boat borrow_net net_snag','net_snag'),
 episode('Free the net and follow a safe route','refuse_yank turn_hoop ease_hoop follow_path','follow_path',offers=('safe_route',)),
 episode('Recover and tether the boat','net_boat return_net tether_boat safe_circle','safe_circle',offers=('recovery','repair'))],
 [state('boat','tethered'),state('net','intact')],tags='recovery care safety'),
'repair':story('Repair the trolley so the load can be moved',[
 episode('Attempt the repair and acknowledge the mistake','cart_goal borrow_spanner tighten_wrongly admit_and_shelter','admit_and_shelter'),
 episode('Diagnose the obstruction and restore the wheel','diagnose_string niko_holds_wheel rafi_holds_wheel refit_and_test','refit_and_test',offers=('transport_ready','repair')),
 episode('Move the load and return the tool','move_plants return_spanner quiet_wheel','quiet_wheel',offers=('delivery',))],
 [state('cart','repaired'),state('wheel','smooth')],tags='repair transport diagnosis delivery'),
'museum':story('Make a controllable shadow demonstration',[
 episode('Try the demonstration and notice the error','exhibit_goal borrow_torch moving_light','moving_light'),
 episode('Control one variable and test again','read_small_print books_support clay_support controlled_trial','controlled_trial',offers=('exhibit_ready','measurement')),
 episode('Invite the visitor to try the demonstration','visitor_turn little_wings','little_wings',offers=('welcome','exhibit_ready'))],
 [state('shadow','small'),state('shadow','controlled'),state('torch','fixed')],tags='exhibit measurement collaboration'),
'laundry':story('Protect the clean washing when the line slips',[
 episode('Notice the unstable washing line','help_washing borrow_pegs slipping_prop ask_help','ask_help'),
 episode('Move and secure the washing together','move_inside fold_sheet drape_sheet catch_sock hang_sock','hang_sock',offers=('shelter','collaboration')),
 episode('Return the pegs and finish sheltering the washing','return_bag sheltered_sock','sheltered_sock',offers=('care',))],
 [state('sheet','secured'),state('sheet','clean'),state('sock','hung')],tags='shelter care collaboration'),
'trail':story('Complete the outing with an accessible route for everyone',[
 episode('Agree on an accessible outing','three_wishes borrow_compass choose_loop blocked_trail','blocked_trail'),
 episode('Find and follow the accessible detour','align_map leni_spots_marker felix_clears_ivy level_detour','level_detour',offers=('safe_route','accessibility')),
 episode('Draw collect the stamp and return the compass','salamander_sketch stamp_card return_compass show_drawing','show_drawing',offers=('artwork','collaboration'))],
 [state('leni','included'),state('book','salamander_drawing'),state('card','complete')],tags='accessibility route artwork'),
'festival':story('Decorate the festival while keeping the gate accessible',[
 episode('Notice that the decoration blocks access','reachable_bunting borrow_string blocked_gate rethink_access','rethink_access'),
 episode('Move and secure the decoration','move_to_fence double_wrap adjust_tension tie_moon hang_flags','hang_flags',offers=('exhibit_ready',)),
 episode('Prove the passage is accessible','clear_passage','clear_passage',offers=('accessibility',))],
 [state('gate','clear'),state('cart','passed_gate')],tags='accessibility exhibit collaboration'),
'biscuit':story('Make a shared thank-you gift from the last dough',[
 episode('Discover the disagreement over the gift','thank_you_gift borrow_cutter torn_dough','torn_dough'),
 episode('Combine both designs in one biscuit','repair_dough cut_together toby_marks_star mara_marks_star','toby_marks_star mara_marks_star',offers=('collaboration',)),
 episode('Bake cool and deliver the gift','bake_biscuit cool_biscuit return_cutter pack_gift sugar_star','sugar_star',offers=('gift','food_ready'))],
 [state('biscuit','baked'),state('biscuit','cool'),state('biscuit','star_mark')],tags='gift collaboration food'),
}

# Fine-event duration overrides; episode estimates are not added to event time.
DURATIONS={
 ('pottery','dry'):{'hour':.2,'day':.8},
 ('pottery','bisque'):{'hour':.9,'day':.1},
 ('pottery','fire'):{'hour':.9,'day':.1},
 ('pottery','cool_bisque'):{'hour':.7,'day':.3},
 ('pottery','cool_final'):{'hour':.7,'day':.3},
 ('biscuit','bake_biscuit'):{'minute':.2,'hour':.8},
 ('biscuit','cool_biscuit'):{'minute':.9,'hour':.1},
}
