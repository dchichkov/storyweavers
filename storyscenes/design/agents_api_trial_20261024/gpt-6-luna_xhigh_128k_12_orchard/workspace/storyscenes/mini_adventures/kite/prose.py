'''Scene-level prose for the orchard adventure; each paragraph follows enacted state.'''


def render(scene_id, before, after):
    if scene_id == 'borrow_basket':
        return ('Mira and Theo reached Ms. Vale’s shed with two slices of bread in Mira’s pocket and an empty lunch cloth. “Could we borrow the picking basket?” Mira asked. Ms. Vale passed it over. “Bring it back clean.” Theo lifted both handles. It would carry their pears while they kept their hands free for careful picking. They walked together into the orchard.')

    if scene_id == 'vignette_crate':
        if after['crate.used_as_table']:
            return ('At the orchard edge, Theo found a wooden crate and pressed one corner. It sat level. “A table, not a ladder,” he said. They spread the lunch cloth across it for sorting. Mira grinned. “Good. I wasn’t planning to climb anything.” The crate waited beside the path, ready to hold their bread.')
        return ('The crate at the orchard edge rocked when Theo tested it. “Not a step,” he said, nudging it aside. Mira spread their cloth on the grass instead. “There. A table that can’t tip.” He laughed, and they left the crate exactly where it was rather than making a risky perch of it.')

    if scene_id == 'vignette_memory':
        return ('While they walked, Mira remembered the pear they had split last summer, juice running down both wrists. “You gave me the bigger half,” Theo said. “You were smaller.” “I still am, according to the old gate.” Mira laughed. The memory made this snack feel like something they were choosing together, not a prize for one of them.')

    if scene_id == 'survey_tree':
        if after['tree.safe_reach']:
            return ('They stopped beneath the tree. The morning was still, and Mira could comfortably reach the lowest ripe pears without stretching onto her toes. Higher fruit stayed out of reach; neither friend considered tugging a limb. “We have enough down here,” Theo said. They looked for firm fruit, not a shortcut.')
        if after['tree.windy']:
            return ('They stopped beneath the tree as a gust set the narrow limbs moving. The ripe cluster bobbed above Mira’s comfortable reach. Theo looked at the shaking leaves, then at a pear resting on the grass. “No climbing, and no pulling,” he said. Mira agreed. “We can make a snack without asking the tree to take a risk.”')
        return ('They stopped beneath the tree. The lower ripe pears hung higher than Mira could comfortably reach, while one sound pear rested on the grass. Theo measured the distance with his eyes. “No climbing, and no pulling,” he said. Mira nodded. “We can make a snack without asking the tree to take a risk.”')

    if scene_id == 'choose_harvest':
        if after['harvest.plan'] == 'low_branch':
            return ('“Those low pears are reachable, but the high ones would mean stretching,” Mira said. Theo tapped the basket’s rim. “We pick what comes away gently and leave the rest.” Mira nodded. They chose the lower cluster, one pear at a time; no crate, shoulder, or branch would become a ladder. The choice cost them the tempting fruit above.')
        reason = 'The leaves are moving, and that cluster can wait.' if after['tree.windy'] else 'The ripe cluster is beyond a comfortable reach.'
        return (f'“Could we shake the branch?” Mira asked. {reason} “No,” Theo said, steady and plain. “The tree doesn’t owe us a snack.” They chose fallen fruit instead. Mira checked it gently for bruises. A smaller harvest was worth more to them than a damaged limb or a pear knocked down in a hurry.')

    if scene_id == 'pick_fruit':
        count = after['harvest.count']
        noun = 'pear' if count == 1 else 'pears'
        if after['harvest.source'] == 'low_branch':
            return (f'Mira turned each low pear upward, the way Ms. Vale had shown her; the stems let go without a jerk. Theo steadied the basket by its rim, not the branch. They gathered {count} ripe {noun}, leaving higher fruit and every leaf untouched. The tree stood just as it had before.')
        return (f'The friends checked the grass beneath the tree and found {count} sound fallen {noun}. Mira wiped away a speck of soil with the cloth; Theo placed them in the basket, not on the limbs above. They left the remaining fruit alone. Nothing was pulled, shaken, or broken.')

    if scene_id == 'share_snack':
        surface = 'the level crate' if after['picnic.surface'] == 'crate' else 'their lunch cloth'
        callback = ('Mira remembered their old picnic; this time Theo passed her an equal half.'
                    if after['friends.memory'] else 'They ate slowly, listening to the leaves.')
        return (f'On {surface}, Mira set out the bread while Theo lifted the fruit from the basket. They cut each pear into equal halves, so both friends received the same sweet share. The basket had carried the harvest safely; now it had done its useful work. {callback}')

    if scene_id == 'ending_full':
        return ('On the way back, they carried the empty basket between them. At the shed, Mira brushed away the leaves and Theo returned it to Ms. Vale. “It carried our snack beautifully,” Mira said. Vale checked the clean weave. “And you left my tree whole.” Their bread-and-pear lunch was finished; the afternoon felt shared.')

    if scene_id == 'ending_small':
        return ('On the way back, they carried the empty basket between them. At the shed, Theo brushed its rim clean and Mira returned it to Ms. Vale. Their single pear had made two bright, sticky halves, and both had eaten. “Small snack, no broken branch,” Theo said. Mira squeezed his hand. It tasted like enough.')

    raise ValueError(f'No prose for scene: {scene_id}')
