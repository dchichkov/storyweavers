'''Short scene prose rendered from the actions and state that actually occurred.'''


def render(scene_id, params, before, after):
    if scene_id == 'borrow_spool':
        return ('Leni found Mrs Bell winding a red-and-white spool beside the village hall. '
                '“Could I borrow it for the welcome bunting? I’ll bring back the leftover string.” '
                'Mrs Bell passed it over. “The spool, please—not the bunting.” Leni looked toward '
                'the bare square posts. They seemed to be waiting for a party.')

    if scene_id == 'meet_neighbor':
        return ('Jo, the new neighbor, sat on the square bench with a walking boot beside them. '
                '“I wanted to help with the festival,” Jo said, “but I’m not climbing anything '
                'until this ankle heals.” Leni started to offer to do it alone, then stopped. '
                '“Would you help me choose where it goes?” Jo smiled. “Now that’s a proper invitation.”')

    if scene_id == 'color_vignette':
        return ('Jo held two paper triangles beside the basket. “Blue and gold. The harbor lanterns '
                'in my old town used those colors.” Leni passed over the yellow pieces. Jo arranged '
                'them without leaving the bench, and Leni carried the choice into their plan. The '
                'bunting would bring a small piece of Jo’s old home into this one.')

    if scene_id == 'knot_vignette':
        if before['knot.slips']:
            return ('“This string slides when it’s wet,” Jo said, rubbing the test knot. Leni almost '
                    'blamed the spool, but Jo showed her a second loop and a firm pull. They practiced '
                    'on a short tail, used ten centimetres, and tested it against the basket handle. '
                    'It held. “A knot you trust is better than a ladder.”')
        return ('Jo suggested testing a knot before trusting it with the bunting. Leni looped the '
                'string twice around a basket handle, and they both leaned back. It held. They used '
                'ten centimetres for the practice, then Jo showed Leni how to keep the loop flat. '
                '“Now we know,” Jo said. Leni liked having checked together.')

    if scene_id == 'choose_layout':
        if after['layout.mode'] == 'square':
            return ('Leni and Jo looked from the arch to the low posts. The square was calm and dry; '
                    'both posts held firm, the spool reached far enough, and Jo could reach the line. '
                    '“No climbing,” Jo said. “We can both reach this.” Leni chose a line fifty-five '
                    'centimetres high. The arch stayed bare, but the square had a plan for both of them.')
        if before['weather.rainy']:
            reason = 'Rain was already stippling the open square'
        elif before['weather.gusty']:
            reason = 'Gusts were tugging at the loose paper triangles'
        elif not before['anchors.sturdy']:
            reason = 'One of the low posts shifted under Leni’s careful test'
        elif before['Jo.reach_cm'] < 55:
            reason = 'Jo could not comfortably reach the square line'
        elif before['spool.remaining_cm'] < 180:
            reason = 'The borrowed string was too short for the exposed square span'
        else:
            reason = 'The unpracticed knot would not stay secure on the exposed line'
        return (f'{reason}. Leni looked up at the arch, then toward the village hall porch. '
                '“We could wait,” she said. Jo pointed to the low rail under the roof. “Or welcome '
                'people now, where I can help.” They carried the basket inside and chose a line '
                'thirty-five centimetres high. The grand arch could stay bare.')

    if scene_id == 'hang_bunting':
        place = 'the square posts' if after['layout.mode'] == 'square' else 'the hall rail'
        height = after['layout.height_cm']
        colors = 'blue and gold' if after['bunting.pattern'] == 'blue-and-gold' else 'red and white'
        knot_line = (' Jo used a double loop on the rail.' if after['knot.reinforced'] and not after['knot.practiced']
                     else ' The knot held when they tested it.' if after['knot.practiced']
                     else ' Their knot held on the first careful tug.')
        return (f'Leni clipped the {colors} triangles along {place}, keeping the line at {height} '
                f'centimetres. Jo tied the final knot from the bench, without climbing or stretching '
                f'for the arch.{knot_line} The borrowed string now had a job: holding the welcome '
                'where both neighbors could reach it.')

    if scene_id == 'welcome':
        location = 'the square' if after['festival.place'] == 'square' else 'the village hall'
        pattern = 'blue-and-gold' if after['bunting.pattern'] == 'blue-and-gold' else 'red-and-white'
        return (f'Mrs Bell opened the doors at {location}, and the first neighbors followed the '
                f'{pattern} bunting to the tables. “We had a grander plan,” Leni said, “but this is '
                'the one we made together.” Jo pointed out a favorite triangle and told its story. '
                'People gathered to listen; the welcome had become something Jo could give, too.')

    if scene_id == 'return_spool':
        return ('After the first rush of the festival, Leni carried Mrs Bell’s spool back to the '
                'hall cupboard, with the unused string wound neatly around it. The used length still '
                'held the bunting in place. “You put it to work,” Mrs Bell said. Jo was showing a '
                'neighbor the knot. Leni was glad to return the spool with something useful left on it.')

    if scene_id == 'ending_square':
        return ('The square filled beneath the low line, and nobody needed a ladder or a rescue. '
                'Jo showed two children how to tie the same secure knot, while Leni welcomed the '
                'late arrivals. The arch remained empty; the square did not. By the time the music '
                'started, Jo was laughing with people who had come to meet their new neighbor.')

    if scene_id == 'ending_hall':
        return ('Rain tapped on the porch while the village hall filled beneath the low bunting. '
                'Jo welcomed the neighbors from the bench and taught a child the double loop. Leni '
                'watched the bare arch through the window and found she did not mind. The festival '
                'had opened on time, the string was doing its job, and Jo belonged in the middle of it.')

    raise ValueError(f'No prose for scene: {scene_id}')
