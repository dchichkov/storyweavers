'''Scene-sized market prose rendered from the committed local-play outcomes.'''


def _weight(units):
    return f'{units / 10:.1f} kg'


def render(scene_id, params, before, after):
    if scene_id == 'market_order':
        return (
            'At the Red Awning, Nella wanted Mr. Rafi to trust her with a morning at the scale. '
            f'Mrs. Vale arrived with an empty basket and an order for {_weight(after["order.units"])} '
            'of apples for the clinic’s tart. Rafi lent Nella his dial scale. '
            '“Bring it back clean—and weighing true,” he said.'
        )
    if scene_id == 'vignette_bruised_apple':
        return (
            'Sam, who lived over the shoe shop, pointed to a bruised apple. '
            '“Mum needs one for stew, not a pretty one.” Nella gave it to him instead of hiding it '
            'under the sound fruit. He ran off pleased; one fewer apple remained for Mrs. Vale’s basket.'
        )
    if scene_id == 'vignette_pear_sample':
        return (
            'Mrs. Vale paused at the adjoining pear crate. Nella cut a thin sample, and her neighbor tasted it. '
            '“Sweeter than I expected,” Mrs. Vale said. She agreed pears could make up a short apple measure '
            'if necessary. Nella marked the sample off the stall’s count; the choice was real, not a free extra.'
        )
    if scene_id == 'fill_order':
        if params.scale_wobbles:
            opening = 'The dial trembled, so Nella tapped its rim until the needle steadied.'
        else:
            opening = 'Nella set fresh brown paper on the clean pan and checked Mrs. Vale’s order slip.'
        if after['scale.reading_units'] == after['order.units']:
            middle = (
                f'She added apples to the requested mark: {_weight(after["scale.reading_units"])}. '
                'The basket looked generous, and the red needle rested exactly on the line.'
            )
        else:
            middle = (
                f'The crate ran low before the needle reached {_weight(after["order.units"])}; '
                f'it stopped at {_weight(after["scale.reading_units"])}. Nella placed the smaller basket beside the slip.'
            )
        return opening + ' ' + middle + ' She liked how a number made a hard job look simple; the answer on the dial seemed certain.'
    if scene_id == 'inspect_scale':
        prefix = 'After another careful tap, ' if params.scale_wobbles else ''
        return (
            f'{prefix}Nella set Mr. Rafi’s iron half-kilo weight on the pan. It should read {_weight(5)}, '
            f'but the needle climbed to {_weight(after["scale.reference_reading_units"])}. '
            'She lifted it and tried again. The same excess returned: the scale added '
            f'{_weight(after["scale.bias_known"])}. The full-looking basket suddenly looked different.'
        )
    if scene_id == 'tell_neighbor':
        short = after['order.units'] - after['order.apples']
        return (
            f'When Mrs. Vale came back, Nella held up the iron weight. “I found the mistake. '
            f'The scale adds {_weight(after["scale.bias_known"])}; your basket is short by {_weight(short)}. '
            'I should have checked before filling it.” Mrs. Vale studied the dial. “Thank you for telling me. '
            'Let’s decide what can honestly go in the tart.”'
        )
    if scene_id == 'conceal_error':
        return (
            'Nella could have explained the extra weight on the dial. Instead, she turned the basket toward '
            'Mrs. Vale and said, “That should be right.” The neighbor trusted the confident voice, paid, and '
            'carried the apples home. Nella watched her go, knowing exactly why the basket had looked full.'
        )
    if scene_id == 'settle_order':
        status = after['order.status']
        concealed = after['helper.decision'] == 'concealed'
        if status == 'full' and concealed:
            return (
                'Mrs. Vale came back holding her kitchen weight. “Your bag was light.” Nella did not blame the dial. '
                'She apologized, reopened the order, and added the missing apples under the checked setting. '
                'Mrs. Vale left with the full basket, but the easy trust between them had gone quiet.'
            )
        if status == 'full':
            return (
                'Mrs. Vale listened without raising her voice. “Then we weigh again, not argue.” Nella added the '
                'missing apples from the crate; a second check confirmed the requested amount. Mrs. Vale paid for '
                'the corrected order and carried it home for the clinic tart.'
            )
        if status == 'mixed' and concealed:
            return (
                'After Mrs. Vale returned with her kitchen weight, Nella admitted she had seen the error and hidden it. '
                'There were not enough apples to replace the whole shortage, so Mrs. Vale accepted pears to complete '
                'the measure. Nella apologized while they weighed the blend together.'
            )
        if status == 'mixed':
            return (
                'There were not enough apples left to top up the basket. Mrs. Vale tasted the pears Nella offered, '
                'then chose the blend for her tart. They weighed the remaining apples and pears to reach the order’s '
                'full amount. “You told me before I had to ask,” she said, and paid.'
            )
        if concealed:
            return (
                'When Mrs. Vale proved the bag light, Nella admitted she had noticed and tried to hide it. '
                'There were not enough apples left, and Mrs. Vale refused pears. Nella returned the payment and '
                'put the basket back on the stall. The order was lost; her apology did not erase it, but she made no excuse.'
            )
        return (
            'The crate was short, and Mrs. Vale would not mix pears into her tart. Nella returned the payment and '
            'put the weighed apples back on the stall. Mrs. Vale left without the ingredients, but thanked Nella '
            'for telling her plainly. Nella felt the lost sale and kept her promise.'
        )
    if scene_id == 'return_scale':
        if params.scale_wobbles:
            first = 'Nella steadied the loose dial and turned its small zeroing screw.'
        else:
            first = 'Nella turned the small zeroing screw back to its proper mark.'
        return (
            f'{first} The needle rested at zero; Mr. Rafi’s half-kilo weight landed exactly on its line. '
            'Nella wiped apple juice from the pan and returned the scale to its owner. Rafi used it at once '
            'to weigh oranges for the next customer. “Useful again,” he said, and Nella could finally breathe.'
        )
    if scene_id == 'ending':
        status = after['order.status']
        concealed = after['helper.decision'] == 'concealed'
        if status == 'full':
            trust = 'The corrected basket was on its way to the clinic; Mrs. Vale’s thanks were brief after she caught the lie.' if concealed else 'Mrs. Vale’s correct basket was on its way to the clinic, and she had not needed to catch the mistake herself.'
            return (
                f'At closing, Mr. Rafi checked the returned scale once more. {trust} '
                'Nella had lost a little time, not her place behind the counter. The next customer watched her '
                'check the dial before she began weighing.'
            )
        if status == 'mixed':
            trust = 'Nella had to meet Mrs. Vale’s eyes while apologizing.' if concealed else 'Mrs. Vale thanked her for speaking up before taking the basket.'
            return (
                f'The clinic tart would have apples and pears instead of apples alone. {trust} '
                'Mr. Rafi’s scale stood true on its hook, and Nella understood that an honest correction could '
                'change an order without making it worthless.'
            )
        trust = 'Mrs. Vale left with her money and no tart ingredients.' if not concealed else 'Mrs. Vale left with her money after Nella admitted the lie.'
        return (
            f'{trust} Nella had no sale to count, only the returned apples and the quiet stall. '
            'Mr. Rafi stayed beside her while she faced the empty space in the order book. '
            'The mistake had cost them dinner plans, but no one had been made to pay for a false measure.'
        )
    raise ValueError(f'No prose for scene: {scene_id}')
