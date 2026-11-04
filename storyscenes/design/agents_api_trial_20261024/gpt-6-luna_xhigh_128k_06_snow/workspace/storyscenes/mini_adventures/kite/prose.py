'''Scene-local prose for the sled errand; outcomes come from enacted state.'''


def render(scene_id, params, before, after):
    if scene_id == 'borrow_sled':
        return ('Snow sifted between the stalls in the village square. Mina needed bread, soup, and lamp oil for Mr. Vale, whose sore knee made the icy walk difficult. Dima, the lending-stall keeper, checked the sled rope. “Bring it back ready for the next errand,” he said. Mina nodded. Jo eyed the empty runners. “One race first?”')

    if scene_id == 'prepare_supplies':
        runner = 'felt loose under her hand' if after['sled.condition'] == 'loose' else 'held straight under her hand'
        return (f'Mina packed the bread, lamp oil, and lidded soup flask together, then tied the basket onto the sled. It weighed {params.load_kg} kilograms. The left runner {runner}. Jo tugged the rope once. “It’ll hold.” Mina checked the knot herself; the flask stood upright between the wrapped loaves.')

    if scene_id == 'mittens_vignette':
        if after['mittens.borrowed']:
            return ('Jo pulled a spare pair of wool mittens from a pocket. “These are mine, so no snowballing.” Mina accepted them and worked each thumb into place. Jo tightened one cuff with a practiced tug. The rope felt rough against the warm wool. “You can have them till we get back,” Jo said. Mina nodded.')
        return ('Mina tugged the thumbs of her own wool mittens straight while Jo checked the sled rope. “Cold hands make bad knots,” Dima called from his stall. Jo held the rope taut; Mina tucked a cuff over her sleeve. The small adjustment took only a moment, but she could feel her grip settle. The basket was ready.')

    if scene_id == 'bell_vignette':
        return ('A brass handbell rang at the bakery door. The baker had just swept a narrow lane toward Mr. Vale’s cottage. Jo peered down it. “Clear all the way to the bend.” Mina could see the clean stripe through the new snow. Jo remembered where it led, and the children returned to the sled with a better route in mind.')

    if scene_id == 'race_decision':
        if after['child.route'] == 'race':
            return ('“Race me to the fountain,” Jo said, bouncing on their toes. Mina looked at the lidded flask and then at the white road. “One run, then straight to Mr. Vale.” Jo’s grin returned. Mina knew a heavy basket could turn a game into a mess, but she chose to try. Jo took the rope beside her.')
        if after['friend.race_pressure'] >= 2:
            return ('“Race me to the fountain,” Jo said, already leaning forward. “Not with Mr. Vale’s soup,” Mina answered. Jo’s grin faded; for a moment they turned toward the other children. Mina kept one hand on the rope. “You can be cross. I still need help.” Jo looked back at the loaded sled, not yet ready to follow.')
        return ('“Race me to the fountain,” Jo said. “Not with Mr. Vale’s soup,” Mina replied. Jo sighed, then took the rope beside her. “All right. But you owe me a race when we’re done.” Mina smiled. The errand came first, and Jo had chosen to come along without making her ask twice.')

    if scene_id == 'journey':
        result = after['child.journey_result']
        if result == 'patient':
            route = ('Jo led Mina down the bakery lane, where the broom had left a clean track.'
                     if after['child.route_taken'] == 'bakery_lane'
                     else 'They followed the square road, pulling steadily through the snow.')
            help_line = ('Jo had stayed behind at first, then caught up and put a shoulder to the handle.'
                         if before['friend.following'] is False
                         else 'Jo took the other side of the rope and matched Mina’s careful pace.')
            cold_line = ('Mina’s fingers began to sting inside her sleeves.'
                         if after['child.hands_cold']
                         else 'Her mittens kept a firm, warm grip on the rope.')
            tired_line = ('Deep snow slowed them until Mina had to stop for a breath.'
                          if after['child.tired']
                          else 'The basket stayed level as the square slipped behind them.')
            return f'{route} {help_line} {cold_line} {tired_line} They did not hurry the soup flask over the ruts, and the sled stayed upright.'
        if result == 'race_clean':
            return ('Jo sprang forward, and Mina kept the sled straight along the flat, swept stretch. The light basket rocked but stayed tied down; the runners held their line. They slowed before the turn to Mr. Vale’s lane, both laughing at their puffing breath. The soup flask was still upright, and the bread had not shifted.')
        cold_line = ('Mina’s bare fingers stung as she hauled the sled upright.'
                     if after['child.hands_cold']
                     else 'Mina’s mittened hands steadied the rope again.')
        repair_line = ('The runner had bent against the rough track.'
                       if after['sled.condition'] == 'needs_repair'
                       else 'The runner still tracked straight, but the jolt shook the basket.')
        return f'Jo sprang forward, and the sled jolted over the rough track. The flask lid popped; soup ran through the basket before they could stop. {repair_line} Bread and oil were still wrapped. Jo knelt to gather them while Mina righted the sled. {cold_line} Their race ended before anyone reached the fountain.'

    if scene_id == 'deliver_supplies':
        if after['neighbor.received_soup']:
            return ('Mr. Vale opened the door before they knocked twice. Mina carried in the bread, soup, and lamp oil; Jo held the empty sled steady outside. He lit his lamp with the oil and smiled at the full basket. “You brought the whole list.” Mina let out the breath she had been holding. Jo finally stopped looking toward the square.')
        return ('Mina showed Mr. Vale the bread and lamp oil, then told him the soup had spilled. Jo did not blame the snow or the sled. Mr. Vale listened, lit his lamp with the oil, and set the bread on his table. “You brought what could be saved, and you came yourselves,” he said. The children carried the useful bundle inside together.')

    if scene_id == 'return_sled':
        repair = ('Dima straightened the runner with his wrench and tested the rope again.'
                  if after['sled.repaired']
                  else 'Dima brushed snow from the runner and found it still straight.')
        mitten_line = ('Jo pulled the borrowed mittens back on, and Mina returned the pair.'
                       if after['mittens.returned']
                       else 'Mina kept her own mittens on against the cold.')
        return f'The walk back seemed shorter with the basket gone. At Dima’s stall, Mina returned the sled that had carried the errand to Mr. Vale’s door. {repair} {mitten_line} Dima set the sled ready for the next neighbor who might need it. Jo stayed beside Mina while she thanked him.'

    if scene_id == 'ending_patient':
        return ('The lamp glowed in Mr. Vale’s window as the square darkened. Mina had kept the soup whole, and Jo had returned when the handle grew hard to pull. “I wanted a race,” Jo said, “but I’m glad I came.” Mina felt proud without pretending she had managed alone. They brushed snow from their sleeves and headed home together.')

    if scene_id == 'ending_race':
        return ('The lamp in Mr. Vale’s window shone through the falling snow. The race had been quick, but stopping at the right turn had mattered more than reaching the fountain first. Mr. Vale had his whole delivery, Dima had a usable sled, and Jo still had enough breath to laugh. Mina went home pleased that excitement and care had fit in the same trip.')

    if scene_id == 'ending_spill':
        return ('Mr. Vale made tea and broke the saved bread while the lamp oil warmed his room. Mina apologized for risking the soup; Jo admitted wanting the race more than wanting to help. Mr. Vale accepted both apologies without pretending the soup had not been lost. They ate together, then returned the repaired sled. The mistake had cost something, but the errand and the friendship were not abandoned.')

    raise ValueError(f'No prose for scene: {scene_id}')
