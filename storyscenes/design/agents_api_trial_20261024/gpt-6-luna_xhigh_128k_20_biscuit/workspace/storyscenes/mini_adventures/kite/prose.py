def render(scene_id, params, before, after):
    if scene_id == 'start':
        return ('Steam fogged the kitchen window while Mum steered a soup pot around the cooling rack. '
                'Mara spotted the last bowl of biscuit dough. “Mrs. Flores lent us her cutters,” she said. '
                '“We can make her a thank-you box.” Eli wiped flour from his nose. “If we split the dough fairly.”')
    if scene_id == 'borrow_cutters':
        condition = ('The star’s bent edge was tacky, so they washed it before carrying it home. '
                     if before['cutters.tacky'] else
                     'The metal was already clean; Eli dried it carefully before they carried it home. ')
        return ('Mara and Eli went next door and asked Mrs. Flores for the star and bell cutters. '
                '“Of course,” she said. “I may bake tonight, so bring them back dry.” '
                + condition + 'Back in their crowded kitchen, the borrowed shapes waited beside the last dough.')
    if scene_id == 'flour_memory':
        return ('Eli dusted a clean patch of counter, then remembered their grandmother letting both children '
                'press cutters into dough. “She never cared if the stars matched,” he said. Mara smiled. '
                '“She cared that we both got a turn.” The memory softened Eli’s voice before either of them '
                'had to argue about the bowl.')
    if scene_id == 'timer_song':
        return ('With the oven warming, Eli tapped a rhythm on the table with a wooden spoon. Mara answered '
                'on the tea tin, quietly enough not to drown Mum’s timer. “Flour on the table, bell in the tin,” '
                'Eli sang. Mara added a rhyme about two good bakers. Their silly song made the wait feel shorter.')
    if scene_id == 'prepare_dough':
        surface = ('Mara dusted the narrow counter with the flour Mum had left out. ' if after['dough.floured']
                   else 'The chilled dough felt firm, though there was no spare flour for the counter. ')
        oven = ('The oven was already warming. ' if before['oven.preheated']
                else 'Mara turned on the oven and waited for it to warm. ')
        texture = ('The dough held its edge when Eli pressed it; they could make neat shapes. '
                   if after['dough.quality'] == 'neat' else
                   'The warm dough clung to their fingers; without flour, clean shapes would be difficult. ')
        return ('Mara brought the last dough to the clear strip of counter. ' + surface + oven + texture
                + 'Eli looked at the small bowl. “That’s all of it,” he said. Neither could count on another batch.')
    if scene_id == 'divide_dough':
        if after['share.plan'] == 'equal':
            callback = ('Eli remembered the old shared trays and relaxed. ' if before['memory.shared'] else '')
            return ('“Half for you, half for me,” Eli said. Mara frowned. “And Mrs. Flores?” '
                    'They weighed the portions, then each set aside an equal part for the thank-you tin. '
                    + callback + 'The rest stayed for their own plate. “If one side is bigger, we fix it,” Mara said. '
                    'Eli steadied the bowl until the scale settled.')
        return ('“The gift should get the larger part,” Mara said. Eli watched her divide the dough. '
                '“Then we share what’s left exactly.” She stopped, listened, and measured again. '
                'They agreed together to send most of the dough next door and keep a smaller piece for themselves. '
                'The choice was generous, but it left no doubt about who had agreed to it.')
    if scene_id == 'bake':
        if after['cookies.gift_ready']:
            song = 'Their timer song kept time while the tray browned. ' if before['kitchen.timer_song'] else ''
            return (song + 'The borrowed star and bell cutters lifted cleanly from the dough. In the oven, '
                    'the edges turned gold. One star lost a point, but the gift portion held together. '
                    'Mara set aside the neat shapes for Mrs. Flores; Eli rescued the smaller home biscuit. '
                    'The cutters came out smeared with dough.')
        reason = ('The warm dough stuck without flour, and the shapes slumped in the oven. '
                  if after['dough.quality'] == 'rough' else
                  'There was too little dough in the gift portion for a proper box of shapes. ')
        return (reason + 'The biscuits still smelled sweet, but none would travel neatly as a gift. '
                'Mara watched a star lose its points. Eli nudged the crumbs into a little pile. '
                '“We can tell her what happened,” he said. The tray was edible, if not what they had planned.')
    if scene_id == 'wrap_box':
        if after['gift.status'] == 'boxed':
            return ('Mara wrote a thank-you card while Eli lined a small tin with clean paper. '
                    'They chose the neatest stars and bells for Mrs. Flores, leaving a little biscuit for home. '
                    'Then dough came off the borrowed cutters under warm water. Eli dried the bent star, '
                    'and Mara checked its edge. The tin and the tools were both ready for the visit.')
        return ('Mara wrote a thank-you card instead of pretending the misshapen biscuits were a present. '
                'Eli folded the note carefully. They would explain that the last dough had gone wrong, and '
                'still say thank you for the loan. After washing and drying the cutters, Mara tested the star '
                'with her thumb. It was clean and ready to work again.')
    if scene_id == 'ending_gift':
        plan = ('They explained that each had given the same amount to the tin. '
                if before['share.plan'] == 'equal' else
                'They explained that they had chosen to give most of the dough to her. ')
        return ('At Mrs. Flores’s kitchen, Mara offered the biscuit tin and Eli held out the card. '
                + plan + 'Mrs. Flores read it, chose the crooked bell as her favorite, and thanked them both. '
                'The siblings split their small home biscuit before leaving. They returned the clean cutters, '
                'and Mrs. Flores pressed the star into dough she had ready for her own baking. It cut cleanly.')
    if scene_id == 'ending_note':
        reason = ('They told Mrs. Flores the warm dough had stuck and the shapes had slumped. '
                  if before['dough.quality'] == 'rough' else
                  'They told Mrs. Flores there had not been enough dough left for a neat gift portion. ')
        return ('At Mrs. Flores’s kitchen, Eli gave her the thank-you note. ' + reason
                + 'She listened without pretending the biscuits were a success. The siblings shared the edible '
                'crumbs, then returned the clean, dry cutters. Mrs. Flores pressed the star into dough she had '
                'ready for her own baking. It cut cleanly. Their thanks had arrived, even without a perfect tin.')
    raise ValueError(f'no prose for scene {scene_id}')
