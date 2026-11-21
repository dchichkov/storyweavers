# Twenty seed stories as executable grammarworlds

16 newly authored worlds plus music, greenhouse, library and pottery cover all twenty Luna seeds. The older rescue, kite and key prototypes remain available separately; runtime total is 23.

460 generated stories, source replay and intact-token annotation checked. 964 negative physical interventions rejected. 23 mapping rules in the joined bank.

These are compact adaptations, not reproductions of the full original prose. Every new world has a physical turn, dialogue, a visible ending and at least two local event alternatives. Typed phrase constructions produce distributions over annotated words. There is no model at runtime.

| World | New | Event kinds covered | Paths | Distinct texts | Mean words | Word-choice steps |
|---|---|---:|---:|---:|---:|---:|
| bakery | yes | 11/11 | 2 | 19 | 86.2 | 6.8% |
| puppets | yes | 10/10 | 2 | 20 | 80.7 | 7.0% |
| greenhouse | existing | 17/17 | 3 | 20 | 107.5 | 8.1% |
| seaside | yes | 9/9 | 2 | 18 | 73.9 | 9.1% |
| library | existing | 21/21 | 13 | 20 | 107.8 | 11.9% |
| snow | yes | 10/10 | 2 | 19 | 81.0 | 7.8% |
| picnic | yes | 11/11 | 2 | 17 | 76.4 | 7.4% |
| music | existing | 16/16 | 3 | 20 | 74.0 | 10.1% |
| market | yes | 11/11 | 2 | 18 | 92.2 | 7.8% |
| camp | yes | 10/10 | 2 | 20 | 74.2 | 12.4% |
| pottery | existing | 26/26 | 6 | 20 | 99.8 | 10.1% |
| orchard | yes | 10/10 | 2 | 19 | 105.2 | 7.5% |
| costume | yes | 11/11 | 2 | 20 | 89.5 | 10.6% |
| pond | yes | 11/11 | 2 | 20 | 99.8 | 7.5% |
| repair | yes | 11/11 | 2 | 20 | 118.4 | 10.2% |
| museum | yes | 9/9 | 2 | 18 | 78.1 | 7.2% |
| laundry | yes | 11/11 | 2 | 20 | 105.4 | 7.0% |
| trail | yes | 12/12 | 2 | 20 | 96.7 | 7.8% |
| festival | yes | 10/10 | 2 | 20 | 104.7 | 6.6% |
| biscuit | yes | 12/12 | 2 | 20 | 116.8 | 8.2% |
| rescue | existing | 13/13 | 2 | 20 | 106.2 | 9.9% |
| kite | existing | 13/13 | 3 | 20 | 74.2 | 10.8% |
| key | existing | 13/13 | 2 | 20 | 78.3 | 13.9% |

## Unfiltered samples and grounded QA

Every example below uses the preselected seed 3007. Full source texts are linked; each annotation document preserves the complete generated story and its token attributes.

### bakery

[Original seed story](/Users/dmitry/storyweavers/storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/01_bakery/story.txt) · [Annotated generated story](bakery.memory.json)

Mr Hobb was lonely. Tessa said, “I want to give the birthday cake to Mr Hobb.” Mrs Pike said, “I need the wicker basket.” Tessa borrowed the wicker basket. The birthday cake was in the wicker basket. Tessa waited beside the paved path. The birthday cake's icing was smudged. Tessa put the birthday cake on the kitchen table. Mr Hobb said, “I am pleased.” He lit the candle. Tessa returned the wicker basket to Mrs Pike. Mr Hobb opened the window. The candle glowed.

Preserved core: An imperfect birthday gift is accepted; the borrowed basket is returned and the dark home gains light.

Local adaptations: Carry on the paved path or wait for the passing cart. The short adaptation returns the basket within the story.

Events: birthday_request → basket_permission → borrow_basket → wait_for_cart → bumped_icing → cake_arrives → imperfect_gift → birthday_light → return_basket → bright_window

Q: What changed at Mr Hobb’s window?
A: Mr Hobb opened his window. The birthday candle glowed beside him.

Q: Who was the birthday cake for?
A: The birthday cake was for Mr Hobb. Tessa wanted to give it to him.

Q: What did Mrs Pike need back?
A: Mrs Pike needed her wicker basket back. Tessa was borrowing it to carry the cake.

Q: How did Tessa carry the cake?
A: Tessa borrowed a wicker basket. The cake traveled in it.

Q: Where did Tessa put the cake?
A: Tessa put the cake on Mr Hobb’s kitchen table. She had carried it in the basket.

Q: Did the imperfect cake spoil the visit?
A: Mr Hobb was pleased with the cake. Tessa had put it on his table.

### puppets

[Original seed story](/Users/dmitry/storyweavers/storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/02_puppets/story.txt) · [Annotated generated story](puppets.memory.json)

The silver star was missing. Lila said, “I need a star.” Nia told Lila, “I can help you.” Lila fetched the needle from the costume shelf. The brass button was heavy. Lila used the needle to stitch the brass button on the felt star. Lila shortened the felt star's loop. Lila said, “I have a light.” Lila put the felt star beside the Moon puppet. Lila returned the needle to the costume shelf. The brass button shone beside the red curtain.

Preserved core: Replace a lost prop with felt and a brass button, secure its loop, perform, return the needle.

Local adaptations: Short loop or double knot.

Events: missing_prop → make_replacement → fetch_needle → sew_button → shorten_loop → speak_up → offer_star → return_needle → last_light

Q: What caught the light at the end?
A: The brass button caught the light beside the red curtain. It decorated the star Lila had made.

Q: What did Lila need for the play?
A: Lila needed a star for the play. The original silver star was missing.

Q: Who offered to help Lila?
A: Nia offered to help Lila. Lila needed a star for the play.

Q: How did Lila decorate the new star?
A: Lila stitched a brass button onto the felt star with a needle. Nia had offered to help her.

Q: How did Lila make the star easier to hold?
A: Lila shortened its loop. The star carried a heavy brass button.

Q: Where did Lila put the new star?
A: Lila put the new star beside the Moon puppet. She had secured its loop.

### greenhouse

[Original seed story](/Users/dmitry/storyweavers/storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/03_greenhouse/story.txt) · [Annotated generated story](greenhouse.memory.json)

Nia wanted to water the sunflower, but the tomato seedlings were thirsty. Mr Bell said, “The tap is broken.” The rain barrel held one can of water. Nia said, “I would like to water the sunflower first.” With the watering can, she watered the sunflower. The shade cloth fell. The tomato seedlings had a brown leaf. Nia secured the umbrella above the tomato seedlings with the garden tie. Mr Bell fixed the tap. Nia watered the tomato seedlings with water from the tap. Mrs Okafor fixed the shade cloth with the clip. Nia said, “I promise I'll water the tomato seedlings first tomorrow.” The brown leaf remained under the repaired shade cloth.

Events: notice → borrow → fill → choose_flower → water_first → shade_break → secure → repair_tap → refill → water_second → repair_shade → return → ending

Q: What did Nia promise after seeing the brown leaf?
A: Nia promised to water the tomato seedlings first tomorrow. The brown leaf remained under the repaired shade cloth.

Q: Who wanted to water the sunflower?
A: Nia wanted to water the sunflower. The tomato seedlings were thirsty too.

Q: What was wrong with the water supply?
A: Mr Bell said the tap was broken.

Q: Where was the first water, and how much was there?
A: The rain barrel held one can of water.

Q: What did Nia use to water the plants?
A: Nia used the watering can to water the sunflower.

Q: Why did Nia secure an umbrella above the seedlings?
A: The shade cloth had fallen. Nia secured an umbrella above the seedlings with a garden tie.

### seaside

[Original seed story](/Users/dmitry/storyweavers/storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/04_seaside/story.txt) · [Annotated generated story](seaside.memory.json)

The sketchbook was windblown. Tessa said, “I want to draw the sea.” Tessa fetched the map from the garden wall. Tessa followed the bathhouse path. Milo said, “I am worried.” The tide was high. Tessa said, “I need to turn.” She checked the map. Tessa and Milo followed the upper path. She drew the sea in the sketchbook. Milo watched the green anemone. The green anemone opened slowly. The sketchbook was still.

Preserved core: Mistake the bathhouse for the rock landmark, turn back before the tide, reach shelter and observe the anemone.

Local adaptations: Milo receives the map or Tessa checks it herself before taking the upper path.

Events: windy_pages → fetch_map → wrong_landmark → rising_water → tessa_checks_map → safe_steps → sheltered_sketch → pool_flower

Q: What changed at the sheltered pool?
A: The green anemone opened slowly. Tessa’s sketchbook stayed still.

Q: What did Tessa want to do?
A: Tessa wanted to draw the sea. Her sketchbook was windblown.

Q: Which wrong path did Tessa follow?
A: Tessa followed the bathhouse path. Milo was worried.

Q: Why did Tessa decide to turn back?
A: The tide was high. Tessa said she needed to turn back.

Q: How did the children leave the unsafe path?
A: Tessa and Milo followed the upper path. The tide below was high.

Q: Who drew while Milo watched the anemone?
A: Tessa drew the sea in her sketchbook. Milo watched the green anemone.

### library

[Original seed story](/Users/dmitry/storyweavers/storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/05_library/story.txt) · [Annotated generated story](library.memory.json)

Mina held a moon atlas, and she wanted to sketch the moon. Jun said, “My whale book is missing.” Mina said, “I promise to help you.” Mina and Jun searched the window nook, but Mina did not locate the whale book. Jun saw the star bookmark on the high shelf. Ms Alvarez reserved the moon atlas for Mina. Using the ladder, Ms Alvarez lifted the whale book down. Ms Alvarez handed the whale book to Jun. Jun told Mina, “I could help you.” Jun opened the moon atlas for Mina. Mina drew the moon from the moon atlas on the paper. Mina showed Jun the moon drawing.

Events: wish → missing → borrow → place_atlas → failed_search → clue → request_help → reserve_atlas → fetch_ladder → retrieve → recognize → checkout → checkout_atlas → return_trolley → return_ladder → share_atlas → sketch_moon → ending

Q: Who reserved the atlas for Mina?
A: Ms Alvarez reserved the moon atlas for Mina.

Q: How did Mina's drawing plan turn out?
A: Mina showed Jun her moon drawing. Ms Alvarez had reserved the atlas for her.

Q: What did Mina want to do?
A: Mina wanted to sketch the moon. She held a moon atlas.

Q: Where did the children search without finding the book?
A: They did not find the book in the window nook. Mina and Jun searched there together.

Q: How did they get the whale book down?
A: Ms Alvarez lifted the whale book down with a ladder. Jun had spotted a star bookmark on the high shelf.

Q: Who promised to help Jun?
A: Mina promised to help Jun. Jun had said his whale book was missing.

### snow

[Original seed story](/Users/dmitry/storyweavers/storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/06_snow/story.txt) · [Annotated generated story](snow.memory.json)

Nia said, “I want to help Mrs Wren.” Tomas told Nia, “I would like to race.” Nia fetched the red sled from the shop. The red sled was stuck. Nia told Tomas, “I need help.” Tomas left the race. Tomas said, “I can help you.” Nia and Tomas freed the red sled. Nia and Tomas cleared the gate. Nia placed the grocery basket on the kitchen table. Nia returned the red sled to the shop. Mrs Wren lit the stove. The stove glowed.

Preserved core: Tomas gives up racing to free Nia’s sled and deliver Mrs Wren’s groceries; her cold home becomes warm.

Local adaptations: Lift or rock the stuck sled free.

Events: delivery_promise → borrow_sled → ice_ridge → leave_race → rock_runner → clear_gate → deliver_food → return_sled → warm_stove

Q: What happened after the delivery?
A: Mrs Wren lit the stove, and it glowed. The grocery basket was on her table.

Q: Who did Nia want to help?
A: Nia wanted to help Mrs Wren. Tomas wanted to race.

Q: Why did Nia ask for help?
A: The red sled was stuck. Nia said she needed help.

Q: How did they get through the gate?
A: Nia and Tomas cleared the gate together. Tomas had stopped to help Nia.

Q: Where did Nia put the groceries?
A: Nia put the grocery basket on the kitchen table. She and Tomas had cleared the gate.

Q: Who offered to help with the stuck sled?
A: Tomas offered to help Nia. Her red sled was stuck.

### picnic

[Original seed story](/Users/dmitry/storyweavers/storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/07_picnic/story.txt) · [Annotated generated story](picnic.memory.json)

Bea said, “I want to welcome Theo.” Sam said, “I am hungry.” Bea borrowed the blue blanket. The welcome sign drifted toward the river. The picnic basket was unsteady. Sam caught the picnic basket. Bea held the blue blanket. Bea fetched the smooth stone. She placed the smooth stone on the blue blanket. She saved the sandwich for Theo. Theo said, “I am sorry.” Sam shared the cookie. Bea and Theo folded the blue blanket.

Preserved core: Protect the picnic instead of chasing the sign toward water; keep a welcome for the delayed guest.

Local adaptations: Theo shares the saved sandwich or Sam shares his cookie. The unreachable sign is not magically recovered.

Events: welcome_plan → borrow_blanket → gust → save_lunch → fetch_weight → secure_blanket → save_portion → late_guest → share_cookie → fold_together

Q: How did the picnic end?
A: Bea and Theo folded the blue blanket together. Bea had saved a sandwich for him.

Q: Who was the picnic for?
A: Bea wanted to welcome Theo. Sam was already hungry.

Q: What happened to the welcome sign and basket?
A: The welcome sign drifted toward the river. The picnic basket became unsteady.

Q: How did they save the picnic?
A: Sam caught the basket while Bea held the blanket. The basket had become unsteady.

Q: Why did Bea save a sandwich?
A: Bea saved a sandwich for Theo. She still wanted to welcome him.

### music

[Original seed story](/Users/dmitry/storyweavers/storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/08_music/story.txt) · [Annotated generated story](music.memory.json)

Nia borrowed the little drum from Dalia, and she hoped to play a duet with Mateo. Nia said, “I need an answering beat.” Mateo said, “I am not ready for the audience.” Mateo said, “I can write a rhythm.” He wrote a rhythm on the paper with the pencil. Nia practiced Mateo's rhythm on the little drum. Nia played Mateo's rhythm on the little drum before Dalia. Mateo clapped, and Nia bowed. Nia said, “I want to play your rhythm again.” Nia put the paper between the little drum and the second drum.

Events: opening → borrow → invite → decline → offer_pattern → write_pattern → prepare_pattern → perform → response → return → ending

Q: How did Mateo respond after Nia played?
A: Mateo clapped, and Nia bowed. Nia had performed before Dalia.

Q: What did Nia hope to do?
A: Nia hoped to play a duet with Mateo. She borrowed the little drum from Dalia.

Q: Who lent Nia the drum?
A: Nia borrowed the little drum from Dalia.

Q: How did Mateo offer to help without performing?
A: Mateo offered to write a rhythm. He had said he was not ready for the audience.

Q: Where did Mateo write the rhythm?
A: Mateo wrote the rhythm on paper with a pencil.

Q: What did Mateo say about playing for an audience?
A: Mateo said he was not ready for the audience. Nia had hoped to play a duet with him.

### market

[Original seed story](/Users/dmitry/storyweavers/storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/09_market/story.txt) · [Annotated generated story](market.memory.json)

Mina said, “I can fill the apple bag.” Mrs Dutta said, “I need to catch the bus.” Mina borrowed the brass scale. Mina weighed the apple bag. Mina located the leaf under the brass scale's pan. The apple bag was underweight. Mina said, “I am wrong.” Mrs Dutta said, “I could wait.” Mina removed the leaf. Mina weighed the apple bag again. The apple bag was full. Mina handed Mrs Dutta the apple bag. Mina returned the brass scale to the olive stall. The brass scale's dial rested at zero.

Preserved core: Inspect the empty scale, admit the bias, remove the obstruction and reweigh before delivery.

Local adaptations: Mina or Aunt Farah removes the leaf.

Events: order_goal → borrow_scale → weigh_order → discover_leaf → admit_error → mina_clears_leaf → correct_weight → deliver_order → return_scale → steady_dial

Q: What did the final scale reading show?
A: The scale’s dial rested at zero. Mina had corrected Mrs Dutta’s order.

Q: Who needed to catch a bus?
A: Mrs Dutta needed to catch a bus. Mina offered to fill her apple bag.

Q: What had affected the scale?
A: Mina found a leaf under the scale’s pan. She had already weighed the apple bag.

Q: How did Mina respond to the mistake?
A: Mina admitted she was wrong. Mrs Dutta said she could wait.

Q: Why did Mina weigh the apples again?
A: Mina weighed the bag again after the leaf was removed. This time the bag was full.

Q: Who removed the trapped leaf?
A: Mina removed the leaf. It had been under the scale’s pan.

### camp

[Original seed story](/Users/dmitry/storyweavers/storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/10_camp/story.txt) · [Annotated generated story](camp.memory.json)

The toy rabbit was missing. Theo said, “I need the toy rabbit.” Nora told Theo, “I can help you.” Nora borrowed the lantern. Theo said, “I am afraid.” She stayed beside Theo. He heard the brass bell. Nora handed Theo the lantern. She freed the toy rabbit from the pine branch. She handed the toy rabbit to Theo. Theo returned the lantern to Dad. Theo held the toy rabbit beside the tent. Theo smiled.

Preserved core: Stay together, use light and the collar/bell clue, free the toy from the path and return the lantern.

Local adaptations: A bell or a blue collar supplies the discovery clue.

Events: missing_rabbit → borrow_lantern → dark_fork → bell_clue → share_light → reach_from_path → return_rabbit → return_light → friendly_shadows

Q: How did Theo finish the search?
A: Theo held the toy rabbit beside the tent and smiled. Nora had freed it from the pine branch.

Q: Who needed the lost toy rabbit?
A: Theo needed his toy rabbit. Nora offered to help him.

Q: Why did Nora stay beside Theo?
A: Theo said he was afraid. Nora stayed beside him.

Q: How did they recover the rabbit?
A: Nora freed the toy rabbit from the pine branch. Theo held the lantern for her.

Q: Who held the lantern for the rescue?
A: Nora gave the lantern to Theo. They stayed together.

### pottery

[Original seed story](/Users/dmitry/storyweavers/storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/11_pottery/story.txt) · [Annotated generated story](pottery.memory.json)

Bea said, “I want to give Grandpa Len a cup.” The cup's handle was wide because Grandpa Len's hand was stiff. The shaping rib slipped, and the cup was dented. Mr Ivo said, “The cup's wall is thick.” Grandpa Len said, “I can hold a bowl with two hands.” Bea said, “I would like a bowl.” Bea reshaped the cup into a bowl with the shaping rib. Mr Ivo fired the bowl twice. The bowl was cool. Bea handed the bowl to Grandpa Len. Grandpa Len poured tea into the bowl. Grandpa Len held the bowl with two hands.

Events: need → goal → shape → slip → inspect → consult → fetch_sponge → remake → return_sponge → return_rib → shelve → dry → load_bisque → bisque → cool_bisque → unload_bisque → glaze → load_final → fire → cool_final → deliver → give → use → ending

Q: How did Bea change her gift design?
A: Bea reshaped the cup into a bowl with the shaping rib. Grandpa Len had said he could hold a bowl with two hands.

Q: What did Grandpa Len do with the bowl at the end?
A: Grandpa Len held the bowl with two hands. Bea had reshaped her cup into the bowl.

Q: Who was Bea making the cup for?
A: Bea was making the cup for Grandpa Len.

Q: Why did the cup have a wide handle?
A: Grandpa Len's hand was stiff. The cup had a wide handle for him.

Q: What happened when the shaping rib slipped?
A: The cup was dented when the shaping rib slipped.

Q: What did Mr Ivo say about the cup's wall?
A: Mr Ivo said the cup's wall was thick.

### orchard

[Original seed story](/Users/dmitry/storyweavers/storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/12_orchard/story.txt) · [Annotated generated story](orchard.memory.json)

Jun said, “I want to give Willa the gift pear.” Tessa told Jun, “I would like to pick a pear.” Tessa borrowed the picking basket. The golden pear was unripe. Jun pulled the picking basket. The high branch was bending. Tessa said, “I need to stop.” He lowered the picking basket. Tessa picked the ripe pear from the low branch. The ripe pear was bruised. Using the picnic knife, Tessa trimmed the ripe pear. Tessa returned the picking basket to the shed. Tessa put the gift pear on the puppet table. The high branch was unbent. The golden pear shone on the high branch.

Preserved core: Protect the branch, pick a reachable ripe fruit, trim its bruise and save a good pear for Willa.

Local adaptations: Tessa picks alone or Jun steadies the picker.

Events: pear_promise → borrow_picker → resisting_fruit → protect_branch → tessa_picks_low → trim_bruise → return_picker → deliver_gift → unbent_branch

Q: What remained in the orchard?
A: The golden pear shone on its unbent branch. The children had lowered the picking basket instead of forcing it.

Q: Who was Jun saving a pear for?
A: Jun wanted to give Willa a pear. Tessa wanted to pick a pear herself.

Q: What was wrong with the high pear?
A: The high pear was unripe. Pulling the picking basket bent its branch.

Q: Why did they lower the picking basket?
A: Tessa said they needed to stop. The high pear was unripe and its branch was bending.

Q: How did Tessa deal with the bruise?
A: Tessa trimmed the ripe pear with her picnic knife. They left the high pear on its branch.

Q: Where did the gift pear go?
A: Tessa put the gift pear on the puppet table. Jun had wanted to save it for Willa.

### costume

[Original seed story](/Users/dmitry/storyweavers/storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/13_costume/story.txt) · [Annotated generated story](costume.memory.json)

Nia said, “I want the golden cape.” Rafi held the Moon robe. Nia borrowed the golden cape. Rafi said, “I need a Sun costume.” Nia handed Rafi the golden cape. The golden cape's hem was long. Nia said, “I can help you.” Rafi gathered the golden cape's front. Nia fetched the Sun disk from the prop box. She handed the Sun disk to Rafi. Rafi raised the Sun disk. She swirled with the blue ribbons. Rafi hung the golden cape in the costume cupboard. The golden cape shone.

Preserved core: Share the cape, gather its trailing hem instead of cutting it, perform with ribbons and return the costume intact.

Local adaptations: Gather the front or lift the hem.

Events: wind_wish → borrow_cape → wrong_costume → share_cape → dragging_hem → gather_front → fetch_sun → give_sun → perform_together → return_costume

Q: What did Nia want to wear?
A: Nia wanted the golden cape. Rafi held a Moon robe.

Q: Why was Rafi unhappy with his costume?
A: Rafi needed a Sun costume. He was holding a Moon robe.

Q: Who gave up the golden cape?
A: Nia gave the cape to Rafi. He needed a Sun costume.

Q: What helped Rafi look like the Sun?
A: Nia gave Rafi the Sun disk. He also had her golden cape.

Q: How did both children take part?
A: Rafi raised the Sun disk. Nia swirled with her blue ribbons.

Q: Where did the cape end up?
A: Rafi hung the cape in the costume cupboard. Its gold still shone.

### pond

[Original seed story](/Users/dmitry/storyweavers/storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/14_pond/story.txt) · [Annotated generated story](pond.memory.json)

The wooden boat drifted toward reeds. Theo said, “I want the wooden boat.” Mina borrowed the long net. The long net snagged on the willow branch. Mina said, “I need to free the long net.” Theo said, “I can wait.” Mina pushed the long net gently. The long net was free. Mina and Theo walked to the stone outlet. She used the long net to lift the wooden boat. She returned the long net to the tool shed. Theo tied the blue cord to the wooden boat. The wooden boat floated on the pond. He held the blue cord.

Preserved core: Stay on the path, avoid breaking the net, follow the boat to calm water, retrieve it and use a tether.

Local adaptations: Turn or gently push the hoop free.

Events: drifting_boat → borrow_net → net_snag → refuse_yank → ease_hoop → follow_path → net_boat → return_net → tether_boat → safe_circle

Q: What was different when the boat floated again?
A: The boat floated while Theo held its blue cord. He had tied the cord to the recovered boat.

Q: What did Theo want back?
A: Theo wanted his wooden boat. It was drifting toward the reeds.

Q: Why did the first attempt stop?
A: The net snagged on a willow branch. Mina was using it to reach the boat.

Q: What did Mina decide to do first?
A: Mina decided to free the net. Theo agreed to wait.

Q: Where did they follow the boat?
A: Mina and Theo walked to the stone outlet. They had freed the snagged net first.

Q: How did Mina free the net?
A: Mina gently pushed the net, and it came free. She had decided to protect it.

### repair

[Original seed story](/Users/dmitry/storyweavers/storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/15_repair/story.txt) · [Annotated generated story](repair.memory.json)

The blue cart was rattling. Ada said, “I want to repair the blue cart.” Niko told Ada, “I need to move the tomato tray.” Ada borrowed the spanner. She used the spanner to tighten the nut. The wheel was locked. Ada said, “I am wrong.” Niko put the tomato tray under the bench. She loosened the nut. She located the kite string inside the wheel. Niko held the wheel. She unwound the kite string. She fitted the wheel. The wheel spun smoothly. Ada and Niko put the tomato tray in the blue cart. She pushed the blue cart to the sheltered corner. Ada returned the spanner to the bench. The tomato tray was sheltered. The wheel was quiet.

Preserved core: Tightening locks the wheel; admit the error, protect the plants, remove trapped kite string and test the repair.

Local adaptations: Niko or Mr Rafi steadies the wheel.

Events: cart_goal → borrow_spanner → tighten_wrongly → admit_and_shelter → diagnose_string → niko_holds_wheel → refit_and_test → move_plants → return_spanner → quiet_wheel

Q: How did the courtyard look at the end?
A: The tomato tray was sheltered, and the cart’s wheel was quiet. Ada had tested the repaired wheel.

Q: Why did Ada want to fix the cart?
A: Ada wanted to repair the cart. Niko needed to move his tomato tray.

Q: What happened when Ada tightened the nut?
A: The wheel locked after Ada tightened its nut. She had used the spanner.

Q: What did they do instead of dragging the cart?
A: Ada admitted she was wrong. Niko put the tomato tray under the bench.

Q: What had caused the rattle?
A: Ada found kite string inside the wheel. Tightening the nut had locked the wheel instead of fixing the problem.

Q: How could Ada tell the repair worked?
A: The wheel spun smoothly after Ada fitted it. The kite string had been removed.

### museum

[Original seed story](/Users/dmitry/storyweavers/storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/16_museum/story.txt) · [Annotated generated story](museum.memory.json)

Miri said, “I want to show Dot a small shadow.” Kit told Miri, “I would like a dragon.” Miri borrowed the torch. Miri moved the torch. The shadow grew. Kit read the instruction label. Miri said, “I need to steady the torch.” Miri steadied the torch with the clay wedge. Miri moved the paper moth toward the screen. The shadow shrank. Dot said, “I can try.” Dot held the paper moth beside the screen. The shadow was small.

Preserved core: Admit the faulty trial, fix the torch position, move only the moth, and let Dot try the corrected demonstration.

Local adaptations: Support the torch on books or with a clay wedge.

Events: exhibit_goal → borrow_torch → moving_light → read_small_print → clay_support → controlled_trial → visitor_turn → little_wings

Q: How did Dot take part?
A: Dot held the moth beside the screen. Its shadow was small.

Q: Who was Miri preparing the exhibit for?
A: Miri wanted to show Dot a small shadow. Kit wanted a dragon.

Q: What went wrong with the first demonstration?
A: The shadow grew while Miri moved the torch. She needed to keep the light still.

Q: What did Miri need to keep still?
A: Miri needed to stop moving the torch. Kit read the instruction label.

Q: What happened with the torch fixed?
A: The shadow shrank when Miri moved the moth toward the screen. The torch stayed fixed.

### laundry

[Original seed story](/Users/dmitry/storyweavers/storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/17_laundry/story.txt) · [Annotated generated story](laundry.memory.json)

Tessa said, “I can hang the white sheet.” Mrs Bell said, “I need the peg bag.” Tessa borrowed the peg bag. The wooden prop was slippery. The washing line was low. Tessa said, “I need help.” Mr Osei said, “I can hold the white sheet.” Tessa and Mr Osei carried the white sheet into the rain shelter. Tessa folded the white sheet. Tessa pegged the white sheet. The little sock slipped. Mr Osei caught the little sock. He hung the little sock beside the white sheet. Tessa gave the peg bag to Mrs Bell. The little sock swung gently. The white sheet was clean.

Preserved core: Ask for help and move clean washing under shelter rather than ignore an unsafe line; return the peg bag.

Local adaptations: Fold or drape the sheet before securing it.

Events: help_washing → borrow_pegs → slipping_prop → ask_help → move_inside → fold_sheet → catch_sock → hang_sock → return_bag → sheltered_sock

Q: What did the sheltered washing look like?
A: The little sock swung gently, and the white sheet stayed clean. Both were protected inside the rain shelter.

Q: Who offered to hang Mrs Bell’s sheet?
A: Tessa offered to hang the sheet. Mrs Bell needed her peg bag back.

Q: What was wrong with the washing line?
A: Its wooden prop was slippery and the line was low. The sheet still needed to be hung.

Q: How did Tessa respond to the slipping prop?
A: Tessa asked for help. Mr Osei offered to hold the sheet.

Q: Where did they take the sheet?
A: Tessa and Mr Osei carried it into the rain shelter. They had asked for help instead of using the low line.

Q: Who got the peg bag back?
A: Tessa gave the peg bag to Mrs Bell. The sheet was now in the shelter.

### trail

[Original seed story](/Users/dmitry/storyweavers/storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/18_trail/story.txt) · [Annotated generated story](trail.memory.json)

Leni used the crutches. Felix said, “I want a stamp.” Leni said, “I need a level path.” Nia borrowed the brass compass. Nia chose the Fern Loop. Nia said, “I can wait.” The fallen birch blocked the path. Using the brass compass, Nia oriented the trail map. Felix lifted ivy. Leni noticed the blue marker. Nia and Felix and Leni followed the level detour. Leni drew the spotted salamander in the sketchbook. Ranger Ivo stamped the discovery card. Nia gave Ranger Ivo the brass compass. Leni showed Ranger Ivo the sketchbook. Felix held the discovery card.

Preserved core: Respect Leni’s pace, align map and compass, find the level detour, observe wildlife, stamp the card and return the compass.

Local adaptations: Leni sees the marker directly or Felix lifts ivy so she can see it.

Events: three_wishes → borrow_compass → choose_loop → blocked_trail → align_map → felix_clears_ivy → level_detour → salamander_sketch → stamp_card → return_compass → show_drawing

Q: What did the friends bring back?
A: Leni showed her drawing to Ranger Ivo. Felix held his completed discovery card.

Q: What did Felix and Leni need?
A: Felix wanted a stamp. Leni needed a level path.

Q: Why did Nia choose the Fern Loop?
A: Leni needed a level path. Nia chose the Fern Loop and said she could wait.

Q: How did Nia check the direction?
A: Nia used the brass compass to orient the trail map. A fallen birch had blocked the path.

Q: Which route did the three friends take around the tree?
A: Nia, Felix and Leni followed the level detour. They had checked the map with the compass.

Q: Who drew the salamander?
A: Leni drew the spotted salamander in her sketchbook. They had found a level detour.

### festival

[Original seed story](/Users/dmitry/storyweavers/storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/19_festival/story.txt) · [Annotated generated story](festival.memory.json)

Rafi was in the wheelchair. Bea said, “I want to hang the paper flags.” Rafi told Bea, “I want to tie the silver moon flag.” Bea borrowed the green string. Bea tied the green string across the entrance. The bread cart was blocked. Rafi said, “I need space.” She untied the green string. Bea carried the green string to the welcome fence. She steadied the green string. Rafi tied the green string. He tied the silver moon flag on the green string. Bea hung the paper flags beside the silver moon flag. Mr Duran pushed the bread cart through the entrance. The silver moon flag shone.

Preserved core: Clear the entrance, relocate to a reachable fence, let Rafi tie his own flag, and prove access with the bread cart.

Local adaptations: Double wrap or adjust tension together.

Events: reachable_bunting → borrow_string → blocked_gate → rethink_access → move_to_fence → adjust_tension → tie_moon → hang_flags → clear_passage

Q: What proved the new arrangement worked?
A: Mr Duran pushed the bread cart through the entrance. Rafi’s moon flag shone beside the other flags.

Q: Who wanted to tie the moon flag?
A: Rafi wanted to tie the moon flag. Bea wanted to hang the paper flags with him.

Q: Why could the bread cart not pass?
A: Bea tied the green string across the entrance. The bread cart was blocked.

Q: How did Bea reopen the entrance?
A: Rafi said they needed space. Bea untied the string across the entrance.

Q: Where did they move the bunting?
A: Bea carried the string to the welcome fence. That left the entrance clear.

Q: Who attached the silver moon flag?
A: Rafi tied the moon flag onto the string himself. The string was at the welcome fence.

### biscuit

[Original seed story](/Users/dmitry/storyweavers/storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/20_biscuit/story.txt) · [Annotated generated story](biscuit.memory.json)

Mr Alvarez located the terrier. Mara said, “I want to thank Mr Alvarez.” Toby told Mara, “I want a dog biscuit.” Toby borrowed the dog cutter. Mara and Toby pulled the last dough lump. The last dough lump was torn. Mara said, “I can share the last dough lump.” She rejoined the last dough lump. Toby guided the dog cutter. She pressed the dog cutter. She handed Toby the star cutter. Toby pressed the star cutter on the dog biscuit. Grandma baked the dog biscuit. The dog biscuit cooled. Toby returned the dog cutter to the cutter tin. Mara put the dog biscuit in the blue tin. Mr Alvarez lifted the dog biscuit. The dog biscuit's star shone.

Preserved core: Rejoin the torn dough, shape a dog with a star impression, bake and cool before packing, and return the borrowed cutter.

Local adaptations: Toby or Mara presses the star mark.

Events: thank_you_gift → borrow_cutter → torn_dough → repair_dough → cut_together → toby_marks_star → bake_biscuit → cool_biscuit → return_cutter → pack_gift → sugar_star

Q: What did Mr Alvarez see on the gift?
A: Mr Alvarez lifted the dog biscuit, and its star shone. Mara and Toby had shaped the gift together.

Q: Who were the biscuits for?
A: Mara wanted to thank Mr Alvarez. Toby wanted to make a dog biscuit.

Q: What happened when they pulled the dough?
A: The last lump tore. Mara and Toby had pulled it in different directions.

Q: How did Mara respond to the torn dough?
A: Mara offered to share it and rejoined the pieces. The last lump had torn during their argument.

Q: How did both children shape the biscuit?
A: Toby guided the dog cutter while Mara pressed it. They had agreed to share the dough.

Q: Who pressed the star mark into the biscuit?
A: Toby pressed the star cutter onto the dog biscuit. The children had shaped it together.

### rescue

Earlier prototype · [Annotated generated story](rescue.memory.json)

Nora wanted to eat the bread, but a puppy shivered on a high ledge. Nora said, “The puppy needs help.” Dad told Nora, “I could lower the basket.” Nora said, “Let me share the bread.” Nora put the bread in the basket. Dad carried the basket to the window, and he lowered the basket to the ledge with the rope. Nora waited because the puppy was frightened. The puppy entered the basket, and it ate the bread. Dad lowered the basket to the garden with the rope. Nora carried the puppy into the cottage, and she wrapped the puppy in the warm blanket. She was hungry, but the puppy rested in the warm blanket.

Events: notice → choose_basket → prepare_basket → load_basket → place_basket → basket_wait → basket_enter → basket_lower → shelter → ending

Q: Why was Nora hungry at the end?
A: The puppy ate the bread that Nora had meant to eat. It rested in the warm blanket after the rescue.

Q: What interrupted the meal?
A: A puppy was shivering on a high ledge. Nora wanted to eat the bread.

Q: Who noticed that the animal needed help?
A: Nora said the puppy needed help.

Q: What did they offer to do?
A: Dad offered to lower a basket. Nora offered to share the bread.

Q: Where did the bread go?
A: Nora put the bread in the basket.

Q: Why did Nora wait?
A: Nora waited because the puppy was frightened.

### kite

Earlier prototype · [Annotated generated story](kite.memory.json)

Nora wanted to fly a kite, but the kite was torn. Nora said, “I would like to repair the kite.” Dad told Nora, “The boat needs a sail.” Nora said, “I want to make a sail.” Dad cut a small sail from the kite with the scissors. Nora tied the sail to the boat with the string. She set the boat on the pond. Nora and Dad watched the boat. The boat sailed across the pond.

Events: notice → inspect → choose_sail → fetch_scissors → cut_sail → attach_sail → launch_boat → ending

Q: What happened to the torn kite at the end?
A: Its paper became the sail on a boat. Nora and Dad watched the boat sail across the pond.

Q: Who wanted to fly the kite?
A: Nora wanted to fly the kite. The kite was torn.

Q: What stopped the kite from flying?
A: The kite was torn.

Q: How did the kite become something useful?
A: Dad cut a small sail from the kite with scissors. The kite had been torn.

Q: Where did Nora put the boat?
A: Nora set the boat on the pond.

Q: What did Dad say the boat needed?
A: Dad said the boat needed a sail.

### key

Earlier prototype · [Annotated generated story](key.memory.json)

Nora wanted to read a storybook inside, but the door was locked. The key was missing. Dad said, “I could help you.” Nora said, “I would like to locate the key.” She fetched the lantern from the porch. With the lantern, she found the key under the bench. She unlocked the door with the key, and she stepped inside the cottage. She hung the key on the hook. She opened the storybook beside Dad.

Events: notice → offer_help → choose_search → fetch_light → find_key → unlock_original → hang_key → ending

Q: What changed by the end?
A: Nora opened the storybook beside Dad. The found key was on the hook.

Q: Who wanted to read inside?
A: Nora wanted to read a storybook inside. The door was locked.

Q: Why could they not open the door?
A: The door was locked, and the key was missing.

Q: Where did the lantern come from?
A: Nora fetched the lantern from the porch.

Q: How was the missing key found?
A: Nora found it under the bench with the lantern. The lantern came from the porch.

Q: Who offered help?
A: Dad offered to help Nora.

## Receiving-world samples

Each source example independently supplies one sampled legal operation into the explicit craft fixture. No event IDs or operation filters are supplied. This demonstrates live reuse; it does not imply every compound event is portable.

- **bakery**: Ada fetched the book from the bench.
- **puppets**: Ada fetched the tape from the bench.
- **greenhouse**: Ada fixed the tap.
- **seaside**: Ada fetched the tape from the bench.
- **library**: Ada fetched the book from the bench.
- **snow**: Ada fetched the tape from the bench.
- **picnic**: Omar fetched the book from the bench.
- **music**: Ada played the drum.
- **market**: Ada fetched the tape from the bench.
- **camp**: Ada fetched the tape from the bench.
- **pottery**: Ada used the shaping rib to shape the cup.
- **orchard**: Ada fetched the tape from the bench.
- **costume**: Ada fetched the book from the bench.
- **pond**: Ada fetched the tape from the bench.
- **repair**: Ada fetched the tape from the bench.
- **museum**: Ada fetched the tape from the bench.
- **laundry**: Ada fetched the tape from the bench.
- **trail**: Ada fetched the tape from the bench.
- **festival**: Ada fetched the tape from the bench.
- **biscuit**: Ada fetched the tape from the bench.
- **rescue**: Ada fetched the ladder from the bench. Ada steadied the ladder.
- **kite**: Omar fetched the ladder from the bench.
- **key**: Ada fetched the tape from the bench.

## Limits

New worlds use authored dependency graphs and physical guards; they are not inferred automatically from raw text. Branches are local and bounded. The original stories are substantially compressed: travel, quantities, timing, social obligations and secondary actions are selectively simplified.
The new mapping rules cover exact single-object fetching, placing and handoffs. Compound diagnosis, cooking, controlled experiments, access decisions and consent are annotated but are not transplanted as arbitrary state changes. Source guard removal is never a substitute for target capability checks.
Some realizations still read as compact action summaries, with repeated names and little sensory detail. Mechanical coverage, replay, dialogue and QA gates do not establish literary quality. No new Luna score is claimed. Future work should extend reusable causal sequences and judge quality/diversity on these new worlds.

## Expanded-pool continuation check

Only the repair-intent prefix was supplied, using the full 460-document archive and seed 7. The remaining actions and STOP were sampled.

Ada said, “I would like to repair the book.” Ada fetched the tape from the bench. Using the tape, she fixed the book.

The repaired-state predicate was satisfied. This is an integration example, not a success-rate or quality estimate. Full probabilities and attributes are in `continuation.json.gz`.

Final verification: 232 regression tests passed; 53,407 annotated tokens reconstructed, 2,700 QA pairs checked, and 964 negative physical interventions rejected. See `completion_audit.json` and `tests.txt`.
