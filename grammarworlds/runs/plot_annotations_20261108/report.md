# Plot annotations on intact story memory

Annotated 400 source documents across 20 worlds: 249 observed fine-event kinds and 46964 tokens. Original prose, text hashes, candidate attribute tables and posterior probabilities were preserved. Twenty fresh live examples also carry proposed plot context before sampling; their text and final physical worlds match the metadata-free baseline.

## Scope

Archetype labels are authored partial analogies, not calibrated probabilities or claims of complete Booker structures. This collection supports quest, mystery and limited comedy analogies; other stories retain their local pattern without an archetype. No example was forced into tragedy, rebirth, rags-to-riches, voyage-and-return, overcoming-the-monster or rebellion. These categories remain available in the inventory but need suitable examples.

Narrative relationships (responds-to, uses-discovery, payoff-of, and similar) are authored interpretations. Native engine dependencies and replayed entity changes are recorded separately. Candidate context sees only prior events; observed consequences occur only in retrospective source annotations. These labels do not yet change event selection or fix story quality.

| World | Local pattern | Partial archetype | Named narrative links in example |
|---|---|---|---:|
| bakery | imperfect_gift_accepted | quest | 3 |
| puppets | loss_replacement_contribution | quest | 4 |
| greenhouse | competing_needs_care_with_consequences | unassigned | 4 |
| seaside | unsafe_route_corrected | quest | 4 |
| library | search_help_and_reciprocity | quest, mystery | 5 |
| snow | temptation_help_delivery | quest | 4 |
| picnic | welcome_despite_disruption | unassigned | 5 |
| music | respect_boundary_change_collaboration | unassigned | 4 |
| market | mistake_diagnosis_honest_repair | mystery | 5 |
| camp | search_without_abandoning_friend | quest, mystery | 4 |
| pottery | failed_attempt_user_led_redesign | quest | 6 |
| orchard | restrain_harm_choose_alternative | quest | 4 |
| costume | competing_wants_shared_solution | comedy | 4 |
| pond | recovery_without_damaging_tool | quest | 4 |
| repair | failed_attempt_diagnosis_changed_approach | mystery | 5 |
| museum | failed_experiment_controlled_retry | mystery | 4 |
| laundry | ask_for_help_protect_shared_work | unassigned | 3 |
| trail | inclusive_route_and_shared_goals | quest | 6 |
| festival | notice_exclusion_redesign_access | unassigned | 4 |
| biscuit | conflict_shared_design_gift | comedy | 4 |

## bakery

Mr Hobb was lonely. Tessa said, “I want to give Mr Hobb the birthday cake.” Mrs Pike told Tessa, “I need the wicker basket.” Tessa borrowed the wicker basket. The birthday cake was in the wicker basket. Tessa waited beside the paved path. The birthday cake's icing was smudged. Tessa placed the birthday cake on the kitchen table. Mr Hobb said, “I am pleased.” He lit the candle. Tessa returned the wicker basket to Mrs Pike. Mr Hobb opened the window. The candle glowed.

| Event | Stage | Narrative role | Earlier narrative evidence |
|---|---|---|---|
| birthday_request | setup | desire | — |
| basket_permission | support | supporting_action | — |
| borrow_basket | support | supporting_action | — |
| wait_for_cart | development | choice | — |
| bumped_icing | complication | setback | — |
| cake_arrives | resolution | payoff | — |
| imperfect_gift | resolution | payoff | payoff_of: birthday_request; reframes: bumped_icing |
| birthday_light | resolution | payoff | — |
| return_basket | support | supporting_action | — |
| bright_window | aftermath | final_image | ending_evidence: birthday_light |

## puppets

The silver star was missing. Lila said, “I need a star.” Nia told Lila, “I could help you.” Lila fetched the needle from the costume shelf. The brass button was heavy. Lila stitched the brass button on the felt star with the needle. Lila tied the felt star's loop twice. Lila said, “I have a light.” Lila put the felt star beside the Moon puppet. Lila returned the needle to the costume shelf. The brass button shone beside the red curtain.

| Event | Stage | Narrative role | Earlier narrative evidence |
|---|---|---|---|
| missing_prop | setup | lack | — |
| make_replacement | development | choice | responds_to: missing_prop |
| fetch_needle | support | supporting_action | — |
| sew_button | development | attempt | — |
| double_loop | development | revision | refines: sew_button |
| speak_up | resolution | decisive_action | — |
| offer_star | resolution | decisive_action | payoff_of: missing_prop |
| return_needle | support | supporting_action | — |
| last_light | aftermath | final_image | ending_evidence: offer_star |

## greenhouse

Nia wanted to water the sunflower, but the tomato seedlings were thirsty. Mr Bell said, “The tap is broken.” The rain barrel held one can of water. Nia told Mr Bell, “I want to water the sunflower first.” Using the watering can, she watered the sunflower. The shade cloth fell. The tomato seedlings had a brown leaf. Nia secured the umbrella above the tomato seedlings with the garden tie. Mr Bell fixed the tap. Nia watered the tomato seedlings with water from the tap. Mrs Okafor fixed the shade cloth with the clip. Nia said, “I promise I'll water the tomato seedlings first tomorrow.” The brown leaf remained under the repaired shade cloth.

| Event | Stage | Narrative role | Earlier narrative evidence |
|---|---|---|---|
| notice | complication | conflict | — |
| borrow | support | supporting_action | — |
| fill | support | supporting_action | — |
| choose_flower | development | choice | responds_to: notice |
| water_first | development | attempt | — |
| shade_break | complication | setback | — |
| secure | development | revision | responds_to: shade_break |
| repair_tap | development | help | — |
| refill | support | supporting_action | — |
| water_second | resolution | payoff | enables: repair_tap |
| repair_shade | development | help | — |
| return | support | supporting_action | — |
| ending | aftermath | final_image | consequence_revisited: water_first |

## seaside

The sketchbook was windblown. Tessa said, “I want to draw the sea.” Tessa fetched the map from the garden wall. Tessa followed the bathhouse path. Milo said, “I am worried.” The tide was high. Tessa said, “I need to turn.” She checked the map. Tessa and Milo followed the upper path. She drew the sea in the sketchbook. Milo watched the green anemone. The green anemone opened slowly. The sketchbook was still.

| Event | Stage | Narrative role | Earlier narrative evidence |
|---|---|---|---|
| windy_pages | setup | desire | — |
| fetch_map | support | supporting_action | — |
| wrong_landmark | complication | failed_attempt | — |
| rising_water | complication | threat | escalates: wrong_landmark |
| tessa_checks_map | development | discovery | responds_to: rising_water |
| safe_steps | resolution | decisive_action | uses_discovery: tessa_checks_map |
| sheltered_sketch | resolution | payoff | payoff_of: windy_pages |
| pool_flower | aftermath | final_image | — |

## library

Mina held a moon atlas. She wanted to sketch the moon. Jun said, “My whale book is missing.” Mina told Jun, “I promise to help you.” Mina and Jun searched the window nook, but Mina did not locate the whale book. Jun noticed the star bookmark on the high shelf. Ms Alvarez reserved the moon atlas for Mina. Using the ladder, Ms Alvarez lifted the whale book down. Ms Alvarez handed Jun the whale book. Jun said, “I can help you.” Jun opened the moon atlas for Mina. Mina sketched the moon from the moon atlas on the paper. Mina showed Jun the moon drawing.

| Event | Stage | Narrative role | Earlier narrative evidence |
|---|---|---|---|
| wish | setup | desire | — |
| missing | setup | lack | — |
| borrow | support | supporting_action | — |
| place_atlas | support | supporting_action | — |
| failed_search | complication | failed_attempt | responds_to: missing |
| clue | development | clue | — |
| request_help | development | choice | — |
| reserve_atlas | development | choice | — |
| fetch_ladder | support | supporting_action | — |
| retrieve | resolution | decisive_action | uses_discovery: clue |
| recognize | resolution | decisive_action | — |
| checkout | resolution | decisive_action | payoff_of: missing |
| checkout_atlas | support | supporting_action | — |
| share_atlas | development | help | reciprocity: checkout |
| return_trolley | support | supporting_action | — |
| return_ladder | support | supporting_action | — |
| sketch_moon | resolution | payoff | payoff_of: wish |
| ending | aftermath | final_image | — |

## snow

Nia said, “I would like to help Mrs Wren.” Tomas said, “I would like to race.” Nia fetched the red sled from the shop. The red sled was stuck. Nia told Tomas, “I need help.” Tomas left the race. Tomas said, “I can help you.” Tomas lifted the red sled. Nia and Tomas cleared the gate. Nia put the grocery basket on the kitchen table. Nia returned the red sled to the shop. Mrs Wren lit the stove. The stove glowed.

| Event | Stage | Narrative role | Earlier narrative evidence |
|---|---|---|---|
| delivery_promise | setup | promise | — |
| borrow_sled | support | supporting_action | — |
| ice_ridge | complication | setback | — |
| leave_race | development | choice | responds_to: ice_ridge |
| lift_runner | resolution | decisive_action | enables: leave_race |
| clear_gate | resolution | decisive_action | — |
| deliver_food | resolution | payoff | payoff_of: delivery_promise |
| return_sled | support | supporting_action | — |
| warm_stove | aftermath | final_image | ending_evidence: deliver_food |

## picnic

Bea said, “I would like to welcome Theo.” Sam said, “I am hungry.” Bea borrowed the blue blanket. The welcome sign drifted toward the river. The picnic basket was unsteady. Sam caught the picnic basket. Bea held the blue blanket. Bea fetched the smooth stone. She put the smooth stone on the blue blanket. She saved the sandwich for Theo. Theo said, “I am sorry.” Sam shared the cookie. Bea and Theo folded the blue blanket.

| Event | Stage | Narrative role | Earlier narrative evidence |
|---|---|---|---|
| welcome_plan | setup | desire | — |
| borrow_blanket | support | supporting_action | — |
| gust | complication | threat | — |
| save_lunch | resolution | decisive_action | responds_to: gust |
| fetch_weight | support | supporting_action | — |
| secure_blanket | resolution | decisive_action | responds_to: gust |
| save_portion | development | choice | goal_progress: welcome_plan |
| late_guest | resolution | payoff | — |
| share_cookie | resolution | payoff | payoff_of: save_portion |
| fold_together | aftermath | final_image | ending_evidence: welcome_plan |

## music

Nia borrowed the little drum from Dalia, and she hoped to play a duet with Mateo. Nia said, “I need an answering beat.” Mateo told Nia, “I am not ready for the audience.” Nia said, “I'll perform a solo.” Nia rehearsed a soft beat and a loud beat. Nia played the solo on the little drum before Dalia. Mateo clapped. Nia bowed.

| Event | Stage | Narrative role | Earlier narrative evidence |
|---|---|---|---|
| opening | setup | desire | — |
| borrow | support | supporting_action | — |
| invite | setup | desire | — |
| decline | complication | conflict | complicates: invite |
| choose_solo | development | choice | responds_to: decline |
| prepare_solo | development | attempt | — |
| perform | resolution | decisive_action | revises_original_goal: opening |
| response | resolution | payoff | — |
| return | support | supporting_action | — |
| ending | aftermath | final_image | ending_evidence: response |

## market

Mina said, “I could fill the apple bag.” Mrs Dutta said, “I need to catch the bus.” Mina borrowed the brass scale. Mina weighed the apple bag. Mina located the leaf under the brass scale's pan. The apple bag was underweight. Mina said, “I am wrong.” Mrs Dutta told Mina, “I can wait.” Aunt Farah removed the leaf. Mina weighed the apple bag again. The apple bag was full. Mina handed the apple bag to Mrs Dutta. Mina returned the brass scale to the olive stall. The brass scale's dial rested at zero.

| Event | Stage | Narrative role | Earlier narrative evidence |
|---|---|---|---|
| order_goal | setup | desire | — |
| borrow_scale | support | supporting_action | — |
| weigh_order | complication | failed_attempt | — |
| discover_leaf | development | discovery | explains_problem: weigh_order |
| admit_error | development | choice | responds_to: discover_leaf |
| farah_clears_leaf | development | revision | — |
| correct_weight | resolution | decisive_action | uses_discovery: discover_leaf |
| deliver_order | resolution | payoff | payoff_of: order_goal |
| return_scale | support | supporting_action | — |
| steady_dial | aftermath | final_image | ending_evidence: correct_weight |

## camp

The toy rabbit was missing. Theo said, “I need the toy rabbit.” Nora said, “I can help you.” Nora borrowed the lantern. Theo said, “I am afraid.” Nora stayed beside Theo. He heard the brass bell. Nora handed Theo the lantern. She freed the toy rabbit from the pine branch. She gave the toy rabbit to Theo. Theo returned the lantern to Dad. Theo held the toy rabbit beside the tent. Theo smiled.

| Event | Stage | Narrative role | Earlier narrative evidence |
|---|---|---|---|
| missing_rabbit | setup | lack | — |
| borrow_lantern | support | supporting_action | — |
| dark_fork | complication | threat | — |
| bell_clue | development | clue | — |
| share_light | development | choice | responds_to: dark_fork |
| reach_from_path | resolution | decisive_action | uses_discovery: bell_clue |
| return_rabbit | resolution | payoff | payoff_of: missing_rabbit |
| return_light | support | supporting_action | — |
| friendly_shadows | aftermath | final_image | ending_evidence: share_light |

## pottery

Bea said, “I want to give Grandpa Len a cup.” The cup's handle was wide because Grandpa Len's hand was stiff. The shaping rib slipped. The cup was dented. Mr Ivo said, “The cup's wall is thick.” Grandpa Len said, “I could hold a bowl with two hands.” Bea said, “I would like a thumb rest.” Using the sponge, Bea shaped the dent into a thumb rest. Mr Ivo fired the cup twice. The cup was cool. Bea handed the cup to Grandpa Len. Grandpa Len poured tea into the cup. Grandpa Len's thumb rested in the thumb rest.

| Event | Stage | Narrative role | Earlier narrative evidence |
|---|---|---|---|
| need | setup | lack | — |
| goal | setup | desire | — |
| shape | development | attempt | — |
| slip | complication | setback | — |
| inspect | development | discovery | responds_to: slip |
| consult | development | discovery | responds_to: slip |
| fetch_sponge | support | supporting_action | — |
| thumb | development | revision | uses_discovery: consult |
| return_rib | support | supporting_action | — |
| return_sponge | support | supporting_action | — |
| shelve | support | supporting_action | — |
| dry | support | supporting_action | — |
| load_bisque | support | supporting_action | — |
| bisque | support | supporting_action | — |
| cool_bisque | support | supporting_action | — |
| unload_bisque | support | supporting_action | — |
| glaze | support | supporting_action | — |
| load_final | support | supporting_action | — |
| fire | resolution | decisive_action | — |
| cool_final | support | supporting_action | — |
| deliver | support | supporting_action | — |
| give | resolution | payoff | payoff_of: goal |
| use | resolution | payoff | payoff_of: need |
| ending | aftermath | final_image | ending_evidence: use |

## orchard

Jun said, “I would like to give Willa the gift pear.” Tessa said, “I want to pick a pear.” Tessa borrowed the picking basket. The golden pear was unripe. Jun pulled the picking basket. The high branch was bending. Tessa said, “I need to stop.” He lowered the picking basket. Tessa picked the ripe pear from the low branch. The ripe pear was bruised. Using the picnic knife, Tessa trimmed the ripe pear. Tessa returned the picking basket to the shed. Tessa put the gift pear on the puppet table. The high branch was unbent. The golden pear shone on the high branch.

| Event | Stage | Narrative role | Earlier narrative evidence |
|---|---|---|---|
| pear_promise | setup | promise | — |
| borrow_picker | support | supporting_action | — |
| resisting_fruit | complication | failed_attempt | — |
| protect_branch | development | choice | responds_to: resisting_fruit |
| tessa_picks_low | development | revision | changes_strategy: protect_branch |
| trim_bruise | development | revision | — |
| return_picker | support | supporting_action | — |
| deliver_gift | resolution | payoff | payoff_of: pear_promise |
| unbent_branch | aftermath | final_image | ending_evidence: protect_branch |

## costume

Nia said, “I would like the golden cape.” Rafi held the Moon robe. She borrowed the golden cape. Rafi said, “I need a Sun costume.” Nia handed the golden cape to Rafi. The golden cape's hem was long. Nia said, “I can help you.” Rafi gathered the golden cape's front. Nia fetched the Sun disk from the prop box. She gave the Sun disk to Rafi. Rafi raised the Sun disk. She swirled with the blue ribbons. Rafi hung the golden cape in the costume cupboard. The golden cape shone.

| Event | Stage | Narrative role | Earlier narrative evidence |
|---|---|---|---|
| wind_wish | setup | desire | — |
| borrow_cape | support | supporting_action | — |
| wrong_costume | complication | conflict | — |
| share_cape | development | choice | responds_to: wrong_costume |
| dragging_hem | complication | setback | — |
| gather_front | development | revision | responds_to: dragging_hem |
| fetch_sun | support | supporting_action | — |
| give_sun | development | help | — |
| perform_together | resolution | payoff | enables: give_sun; revises_original_goal: wind_wish |
| return_costume | aftermath | final_image | — |

## pond

The wooden boat drifted toward reeds. Theo said, “I would like the wooden boat.” Mina borrowed the long net. The long net snagged on the willow branch. Mina told Theo, “I need to free the long net.” Theo told Mina, “I could wait.” Mina turned the long net gently. The long net was free. Mina and Theo walked to the stone outlet. She used the long net to lift the wooden boat. She returned the long net to the tool shed. Theo tied the blue cord to the wooden boat. The wooden boat floated on the pond. He held the blue cord.

| Event | Stage | Narrative role | Earlier narrative evidence |
|---|---|---|---|
| drifting_boat | setup | lack | — |
| borrow_net | support | supporting_action | — |
| net_snag | complication | setback | — |
| refuse_yank | development | choice | responds_to: net_snag |
| turn_hoop | development | revision | changes_strategy: refuse_yank |
| follow_path | development | attempt | — |
| net_boat | resolution | decisive_action | payoff_of: drifting_boat |
| return_net | support | supporting_action | — |
| tether_boat | resolution | payoff | — |
| safe_circle | aftermath | final_image | ending_evidence: tether_boat |

## repair

The blue cart was rattling. Ada said, “I would like to repair the blue cart.” Niko told Ada, “I need to move the tomato tray.” Ada borrowed the spanner. With the spanner, she tightened the nut. The wheel was locked. Ada said, “I am wrong.” Niko placed the tomato tray under the bench. Ada loosened the nut. She found the kite string inside the wheel. Mr Rafi held the wheel. She unwound the kite string. She fitted the wheel. The wheel spun smoothly. Ada and Niko put the tomato tray in the blue cart. Ada pushed the blue cart to the sheltered corner. She returned the spanner to the bench. The tomato tray was sheltered. The wheel was quiet.

| Event | Stage | Narrative role | Earlier narrative evidence |
|---|---|---|---|
| cart_goal | setup | desire | — |
| borrow_spanner | support | supporting_action | — |
| tighten_wrongly | complication | failed_attempt | — |
| admit_and_shelter | development | choice | responds_to: tighten_wrongly |
| diagnose_string | development | discovery | explains_problem: tighten_wrongly |
| rafi_holds_wheel | development | help | — |
| refit_and_test | resolution | decisive_action | uses_discovery: diagnose_string |
| move_plants | resolution | payoff | payoff_of: cart_goal |
| return_spanner | support | supporting_action | — |
| quiet_wheel | aftermath | final_image | ending_evidence: refit_and_test |

## museum

Miri said, “I would like to show Dot a small shadow.” Kit said, “I want a dragon.” Miri borrowed the torch. Miri moved the torch. The shadow grew. Kit read the instruction label. Miri said, “I need to steady the torch.” Miri rested the torch on the book stack. Miri moved the paper moth toward the screen. The shadow shrank. Dot said, “I could try.” Dot held the paper moth beside the screen. The shadow was small.

| Event | Stage | Narrative role | Earlier narrative evidence |
|---|---|---|---|
| exhibit_goal | setup | desire | — |
| borrow_torch | support | supporting_action | — |
| moving_light | complication | failed_attempt | — |
| read_small_print | development | discovery | responds_to: moving_light |
| books_support | development | revision | uses_discovery: read_small_print |
| controlled_trial | resolution | decisive_action | enables: books_support |
| visitor_turn | resolution | payoff | — |
| little_wings | aftermath | final_image | payoff_of: exhibit_goal |

## laundry

Tessa said, “I could hang the white sheet.” Mrs Bell said, “I need the peg bag.” Tessa borrowed the peg bag. The wooden prop was slippery. The washing line was low. Tessa said, “I need help.” Mr Osei said, “I can hold the white sheet.” Tessa and Mr Osei carried the white sheet into the rain shelter. Tessa draped the white sheet. Tessa pegged the white sheet. The little sock slipped. Mr Osei caught the little sock. He hung the little sock beside the white sheet. Tessa gave the peg bag to Mrs Bell. The little sock swung gently. The white sheet was clean.

| Event | Stage | Narrative role | Earlier narrative evidence |
|---|---|---|---|
| help_washing | setup | desire | — |
| borrow_pegs | support | supporting_action | — |
| slipping_prop | complication | setback | — |
| ask_help | development | choice | responds_to: slipping_prop |
| move_inside | development | revision | changes_strategy: ask_help |
| drape_sheet | development | revision | — |
| catch_sock | development | help | — |
| hang_sock | resolution | payoff | — |
| return_bag | support | supporting_action | — |
| sheltered_sock | aftermath | final_image | payoff_of: help_washing |

## trail

Leni used the crutches. Felix said, “I want a stamp.” Leni said, “I need a level path.” Nia borrowed the brass compass. Nia chose the Fern Loop. Nia said, “I can wait.” The fallen birch blocked the path. Nia oriented the trail map with the brass compass. Felix lifted ivy. Leni spotted the blue marker. Nia and Felix and Leni followed the level detour. Leni drew the spotted salamander in the sketchbook. Ranger Ivo stamped the discovery card. Nia handed Ranger Ivo the brass compass. Leni showed Ranger Ivo the sketchbook. Felix held the discovery card.

| Event | Stage | Narrative role | Earlier narrative evidence |
|---|---|---|---|
| three_wishes | setup | desire | — |
| borrow_compass | support | supporting_action | — |
| choose_loop | development | choice | — |
| blocked_trail | complication | setback | — |
| align_map | development | clue | responds_to: blocked_trail |
| felix_clears_ivy | development | clue | — |
| level_detour | resolution | decisive_action | uses_discovery: align_map; uses_discovery: felix_clears_ivy |
| salamander_sketch | resolution | payoff | payoff_of: three_wishes |
| stamp_card | resolution | payoff | payoff_of: three_wishes |
| return_compass | support | supporting_action | — |
| show_drawing | aftermath | final_image | ending_evidence: level_detour |

## festival

Rafi was in the wheelchair. Bea said, “I would like to hang the paper flags.” Rafi told Bea, “I would like to tie the silver moon flag.” Bea borrowed the green string. She tied the green string across the entrance. The bread cart was blocked. Rafi said, “I need space.” Bea untied the green string. Bea carried the green string to the welcome fence. Rafi tied the green string twice. He tied the silver moon flag on the green string. Bea hung the paper flags beside the silver moon flag. Mr Duran pushed the bread cart through the entrance. The silver moon flag shone.

| Event | Stage | Narrative role | Earlier narrative evidence |
|---|---|---|---|
| reachable_bunting | setup | desire | — |
| borrow_string | support | supporting_action | — |
| blocked_gate | complication | failed_attempt | — |
| rethink_access | development | choice | responds_to: blocked_gate |
| move_to_fence | development | revision | changes_strategy: rethink_access |
| double_wrap | development | revision | — |
| tie_moon | resolution | payoff | payoff_of: reachable_bunting |
| hang_flags | resolution | payoff | — |
| clear_passage | aftermath | final_image | ending_evidence: blocked_gate |

## biscuit

Mr Alvarez discovered the terrier. Mara said, “I would like to thank Mr Alvarez.” Toby said, “I would like a dog biscuit.” Toby borrowed the dog cutter. Mara and Toby pulled the last dough lump. The last dough lump was torn. Mara said, “I could share the last dough lump.” Mara rejoined the last dough lump. Toby guided the dog cutter. She pressed the dog cutter. She gave Toby the star cutter. Toby pressed the star cutter on the dog biscuit. Grandma baked the dog biscuit. The dog biscuit cooled. Toby returned the dog cutter to the cutter tin. Mara put the dog biscuit in the blue tin. Mr Alvarez lifted the dog biscuit. The dog biscuit's star shone.

| Event | Stage | Narrative role | Earlier narrative evidence |
|---|---|---|---|
| thank_you_gift | setup | desire | — |
| borrow_cutter | support | supporting_action | — |
| torn_dough | complication | conflict | — |
| repair_dough | development | choice | responds_to: torn_dough |
| cut_together | resolution | decisive_action | changes_strategy: repair_dough |
| toby_marks_star | development | help | — |
| bake_biscuit | support | supporting_action | — |
| cool_biscuit | support | supporting_action | — |
| return_cutter | support | supporting_action | — |
| pack_gift | resolution | payoff | payoff_of: thank_you_gift |
| sugar_star | aftermath | final_image | ending_evidence: toby_marks_star |

Artifacts: `stories.memory.jsonl.gz` retains the full annotated pool; `live_candidates.jsonl.gz` records fresh generated token distributions; `summary.json` records counts.
