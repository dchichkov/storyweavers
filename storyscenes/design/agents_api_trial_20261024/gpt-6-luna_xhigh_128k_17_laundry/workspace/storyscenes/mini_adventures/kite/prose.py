'''Scene prose rendered from enacted local outcomes, not whole-story variants.'''


def _callbacks(state):
    parts = []
    if state['snail.safe']:
        parts.append('Nia remembered the snail tucked safely beneath the marigolds.')
    if state['child.remembers_rhyme']:
        parts.append('Mae’s rhyme came back to her: “Corners first, corners last.”')
    return ' '.join(parts)


def render(scene_id, params, before, after):
    if scene_id == 'borrow_bag':
        return ('Mae was sorting the line’s last dry socks when Nia arrived with an empty laundry basket. '
                '“Could I borrow your peg bag? Mum says a shower is coming, and I can finish your wash first.” '
                'Mae lifted the canvas bag from the bench. “Take it, but bring it back. Don’t trust that blue sky.”')
    if scene_id == 'sky_signs':
        return ('Nia pinched the air; it smelled of wet soil. Beyond the roofs, a grey strip was gathering, '
                'though sunlight still rested on Mae’s towels. “How long?” Nia asked. Mae watched a leaf turn '
                'its pale side upward. “Not long enough to admire the clouds. Sort the sheet first.”')
    if scene_id == 'save_snail':
        return ('A snail was inching toward a puddle on the path. Nia could have stepped around it and started '
                'straight away. Instead, she lifted it on a fallen leaf and set it beneath the marigolds. '
                '“You’re slower than the weather,” she whispered. From the shed, Mae called, “That makes two of us.”')
    if scene_id == 'peg_rhyme_vignette':
        return ('Mae tapped the canvas bag. “Corners first, corners last. Check the sheet twice.” Nia repeated '
                'the rhyme, giving the final word a drumbeat. “You’ve been saving that for me.” “Since Tuesday,” '
                'Mae said. Her grin made the job feel less like a test, and Nia tucked the rhyme away with the pegs.')
    if scene_id == 'prepare_wash':
        if after['child.priority'] == 'sheet':
            decision = '“Sheet first,” Nia decided. “It catches the most wind.”'
        else:
            decision = '“The little things first,” Nia decided. “They’ll be quick to secure.”'
        return ('Nia pressed the line with one finger; it dipped slightly but held. Mae showed her the sheet, '
                'shirt, towel and socks. “A heavy sheet needs a strong line,” she warned. ' + decision +
                ' Nia counted the pegs and set the basket within reach.')
    if scene_id == 'hang_wash':
        names = {'sheet': 'the sheet', 'shirt': 'the shirt', 'towel': 'the towel', 'socks': 'the socks'}
        hung = [names[item] for item in ('sheet', 'shirt', 'towel', 'socks') if after[f'{item}.location'] == 'line']
        waiting = [names[item] for item in ('sheet', 'shirt', 'towel', 'socks') if after[f'{item}.location'] == 'basket']
        if hung:
            first = 'Nia clipped ' + ', '.join(hung) + ' to the line.'
        else:
            first = 'Nia kept the washing in the basket rather than waste a peg.'
        if waiting:
            second = ' ' + ' '.join(waiting).capitalize() + (' stayed in the basket.' if len(waiting) == 1 else ' stayed in the basket.')
        else:
            second = ' The basket was empty.'
        if after['sheet.location'] == 'line':
            detail = f' She used {after["sheet.pegs"]} pegs on the sheet’s corners.'
        elif params.sheet_heavy and not params.line_strength:
            detail = ' The weak line could not safely take the heavy sheet, so it stayed folded.'
        else:
            detail = ' The sheet stayed folded when the remaining pegs could not secure it.'
        return (first + detail + second + ' Each clip made the bag lighter; a gust made the line hum just as Nia finished.')
    if scene_id == 'weather_turn':
        if after['child.choice'] == 'leave':
            return ('The sheet’s corners held, and every smaller piece was on the strong line. Nia gave the clips '
                    'one careful tug. No drops had landed yet. “It can stay there,” she said, resisting the urge '
                    'to move everything just because the clouds looked serious. Mae nodded toward the shed anyway.')
        if after['child.choice'] == 'shelter':
            weather = 'Rain had begun to patter on the path.' if after['weather.raining'] else 'The dark cloud was nearly over the fence.'
            return (weather + ' The sheet snapped once, and the line bowed under the load. Nia looked at the '
                    'covered rack, then at Mae. “Let’s use the shed before this turns into a sail.” Mae held '
                    'the door ready; Nia chose to save the whole wash under cover.')
        weather = 'The first drops were already darkening the path.' if after['weather.raining'] else 'The shower was close enough to make the leaves turn.'
        return (weather + ' The line was not safe, and there was no open covered rack. “Basket, now,” Nia said. '
                'She chose to gather the washing rather than pretend the pegs could hold everything. Mae moved '
                'the empty basket within reach while the wind rattled the fence.')
    if scene_id == 'protect_wash':
        if after['wash.resolution'] == 'line':
            return ('Nia checked the sheet’s corners and the smaller clothes once more. The line held steady; '
                    'the shower had not arrived. “I thought I’d have to rescue it,” she said. Mae looked at the '
                    'full, secure line. “You did the work carefully. Now we can leave it there.”')
        if after['wash.resolution'] == 'shelter':
            weather = 'Rain drummed on the shed roof.' if after['weather.raining'] else 'The grey edge of the shower reached the garden.'
            return (weather + ' Mae held the shed door while Nia carried every garment to the covered rack. '
                    'Some pieces still had pegs; the rest could lie over the bars. “Not the sunny line I wanted,” '
                    'Nia said, “but nothing’s out in the rain.” Mae agreed.')
        return ('The rain arrived as Nia gathered the clothes. She unclipped the borrowed pegs, returned them to '
                'the bag, and tucked every garment into the basket. The sheet’s edge was damp, but none of the '
                'wash was left flapping on the line. “I missed the deadline,” she said. “We can still put it right,” Mae answered.')
    if scene_id == 'ending_line':
        extra = _callbacks(after)
        return ('Mae took the peg bag back and looked along the complete, steady line. “You finished before the '
                'shower,” she said. Nia was pleased, but more pleased that the sheet was not dragging in the soil. '
                'The spare pegs went home in the bag; the others stayed at work on Mae’s washing. ' + extra).strip()
    if scene_id == 'ending_shelter':
        extra = _callbacks(after)
        weather = 'The shower tapped the shed roof.' if after['weather.raining'] else 'The cloud hung over the garden.'
        return (weather + ' Mae took the peg bag back while Nia checked the sheltered rack. They had not beaten '
                'the weather to the line, but every garment was safe and the bag had done its job. “That counts,” '
                'Mae said. Nia nodded; it was a different finish, not a pretend one. ' + extra).strip()
    if scene_id == 'ending_rain':
        extra = _callbacks(after)
        return ('Nia told Mae she had missed the shower. Together they moved the damp washing onto Mae’s indoor '
                'rack, using Mae’s household clips, then returned the borrowed bag with its pegs recovered. '
                '“You told me what happened and helped me fix it,” Mae said. Nia’s sleeve was wet, but the wash '
                'was no longer stranded in the rain. ' + extra).strip()
    raise ValueError(f'No prose for scene: {scene_id}')