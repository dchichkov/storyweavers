"""Authored encounters; only committed state selects prose and callbacks."""


def render(scene, before, after):
    if scene == "launch":
        return ('Nell hid a paper crown under the village bakery counter. Tomorrow Mr Vale '
                'was retiring to the sea; tonight the village would surprise him with supper. '
                'Their plaited loaf waited in its tin. The windowless oven-room bulb had failed; '
                'the baker was fetching another from town. '
                '"His lantern," Kit suggested. "Ask without telling," Nell said. "Seven o\'clock. Not a word."')
    if scene == "borrow":
        return ('They crossed the lane to the workshop. "Could we borrow your lantern? Our bulb\'s gone," '
                'Nell asked. Vale lifted it off its hook. "Bring it back before I lock up. I need it '
                'for the cellar steps. Leave oil for them." Nell took the handle. Back across the lane, Kit held '
                'the bakery door for her and the borrowed light.')
    if scene == "glove":
        return ('A customer had left a green wool glove by the till. Kit tried it on; the empty '
                'fingers dangled beyond his own. "I could carry five more fingers in here." Nell '
                'laughed and pinned it to the noticeboard. "Leave some room for the owner." Kit '
                'tucked its thumb into its palm, making it wave at tomorrow\'s customers.')
    if scene == "darn":
        return ('They unfolded the supper cloth. A blue darn crossed one corner. Nell turned it '
                'toward the wall, but Kit turned it back. "He fixes things. He won\'t mind a mend." '
                'She smoothed the corner beside the head chair. The blue stitches looked almost '
                'like a small ladder, going nowhere in particular. She left them showing.')
    if scene == "crown":
        return ('Nell retrieved the crown and read VALE aloud. "He knows his name," Kit said. '
                '"It\'s on all his parcels." She turned the paper over and wrote THANK YOU on '
                'the other side. Kit held it against the empty head chair. "Better." Nell put '
                'it back under the counter before anyone could look through the window.')
    if scene == "refill":
        return ('The lantern was still cold. Kit found a little bottle of lamp oil behind the '
                'till. Nell unscrewed the reservoir and poured in the last of it, keeping the '
                'spout against the rim. "That was all," Kit said, tipping the empty bottle. '
                'She tightened the cap. "Then we\'ll have to make it last."')
    if scene == "inspect_wick":
        detail = ('It refused to turn. "We\'ll have to ease that before lighting it," Nell said.'
                  if before["lantern.wick_stuck"] else
                  'It turned smoothly, lifting a little black edge. "That works," Nell said.')
        return ('Kit pointed to the lantern\'s brass wheel. "Is that the light?" Nell tried it '
                'while the glass was cold. ' + detail +
                ' Kit put his hands in his pockets. "I thought you just asked it nicely." '
                '"You can try that with the oven."')
    if scene == "window_note":
        return ('Kit read the little supper notice propped in the window. "Not a word, you said." '
                'Nell snatched it down and slid a bread-price card in front of it. Across the '
                'lane the workshop window reflected the sky; she could not tell whether Vale '
                'had looked. "We are extremely good at secrets," Kit whispered to the price card.')
    if scene == "mend_crown":
        return ('One tooth of the paper crown hung by a thread. Kit found a clean paper strip; '
                'Nell pasted it behind the tear and held the edges together. "Don\'t breathe on '
                'the king," she said. Kit held his breath until she laughed. The tooth stood '
                'upright again, with a pale seam running down its back.')
    if scene == "bake":
        if before["lantern.wick_stuck"]:
            wheel = ('As she had found, the wheel stuck.' if before["nell.knows_wick"] else
                     'The wheel stuck when she tried it.')
            wheel += ' She eased the bent guard aside; it turned.'
        else:
            wheel = 'She turned the wheel; the wick rose.'
        if not after["oven.on"]:
            return ('Nell checked the oil before carrying the lantern into the oven room. ' + wheel +
                    ' "Only enough for his cellar," she said. Kit stopped with his hands on the '
                    'loaf tin. "So we wait?" She left the lantern unlit. The loaf stayed outside '
                    'the oven; even the first ten minutes would use Vale\'s share.')
        return ('Nell checked the oil, then carried the lantern into the oven room. ' + wheel +
                ' She lit it and set it on the stone shelf, clear of the towels. Kit helped '
                'slide the loaf into the oven. "Everybody\'s bread," he said. Nell closed the '
                'door gently. For ten minutes the plaits swelled in the heat.')
    if scene == "knock":
        demand = ('"The furniture van\'s early. I need my lantern now," Vale said.' if before["vale.early_van"] else
                  '"Nearly locking-up time. May I have my lantern?" Vale asked.')
        start = ('Nell extinguished the lantern and carried it out to answer.' if before["oven.on"] else
                 'Nell carried the unlit lantern out to answer.')
        loaf = ('The loaf needed ten more minutes.' if before["oven.on"] else
                'The loaf had not even entered the oven.')
        return ('A knock reached them from the bakery. ' + start + ' ' + demand +
                ' ' + loaf + ' Kit looked at Nell, then at the crown beneath the counter. '
                'She kept her hand around the borrowed handle.')
    if scene == "confess":
        if before["vale.early_van"]:
            return ('"It\'s a loaf for your leaving supper," Nell said. "Could you stay?" Vale '
                    'took his cap off, then looked across the lane. "Even for this, I can\'t '
                    'keep the furniture van waiting." She handed him the lantern. He checked '
                    'its moving wick and remaining oil. "Enough for the steps. Thank you." He '
                    'went back to his workshop.')
        return ('"There\'s a loaf for your leaving supper," Nell said. "It was meant to be a surprise." '
                'Vale took off his cap. Kit stopped hiding the crown. "Could you stay and help?" '
                'Nell asked. "Ten minutes," Vale said. "But leave oil for my steps." '
                'The secret was out; the oil was still borrowed.')
    if scene == "request_extension":
        if before["vale.early_van"]:
            return ('"Could we keep it longer?" Nell asked, standing between Vale and the crown. '
                    'He shook his head. "The furniture van won\'t wait while I empty the cellar." '
                    'She returned the lantern; he checked the wick and the oil for his steps. '
                    'He crossed back to the workshop. "He still doesn\'t know," Kit said. Nell '
                    'wished that felt better.')
        return ('"Could we keep it a little longer?" Nell asked. "Then I\'ll bring it straight over." '
                'Vale checked his watch. "Ten. I can pack the counter first." He went back '
                'across the lane, leaving the lantern in her hand. Kit let out his breath. '
                'Nell held up both hands, counting the minutes on her fingers.')
    if scene == "return_now":
        return ('Nell gave the lantern back. Vale checked its wick and remaining oil. '
                '"Enough for the cellar," he said, carrying it across to his workshop. '
                '"What about the loaf?" Kit asked. Nell looked toward the dark oven-room '
                'doorway. "We won\'t use his last oil on it." She rubbed the crease '
                'the handle had left in her palm, then let her hand fall.')
    if scene in ("finish_secret", "finish_together"):
        start = ('Vale followed them into the oven room. Nell gave him the lantern; he held it '
                 'while she relit it.' if scene == "finish_together" else
                 'They carried the lantern back into the oven room and relit it. Kit watched the clock.')
        return (start + ' After ten minutes Nell opened the oven and tapped the loaf: hollow. '
                'Together they lifted it onto the rack, turned the oven off, and extinguished '
                'the light. Using towels around the hot tin, Kit carried the loaf to the table.')
    if scene == "postpone":
        reason = ('Only Vale\'s cellar oil remained.' if before["lantern.fuel"] == before["loan.reserve"] else
                  'They could not keep the light any longer.')
        stopping = ('Nell went in and switched the oven off.' if before["oven.on"] else
                    'Nell checked the oven was still off.')
        return (reason + ' ' + stopping +
                ' Back at the counter she left the baker a note: Can this loaf be saved? '
                'Then she wrote Vale another: Breakfast before you leave tomorrow, if we can '
                'manage it? Kit read both. "Don\'t promise bread yet." She underlined the question mark.')
    if scene == "ending_secret":
        detail = ' The blue darn lay beside his plate.' if before["cloth.darn_visible"] else ''
        return ('They returned the lantern across the lane. Vale checked its wick and cellar oil, '
                'then followed their invitation back. At the bakery Nell stepped aside: the loaf '
                'stood on the table. "For me?" Kit offered the crown.' + detail +
                ' Vale rested the lantern at his place while Kit broke the heel. '
                '"Keep me the crust," he said.')
    if scene == "ending_together":
        detail = ' He rested his wrist beside the blue darn.' if before["cloth.darn_visible"] else ''
        return ('Vale turned the wick wheel and checked the oil. "Enough for your steps?" Nell asked. '
                '"Enough." He rested the lantern at his place and broke the heel. "Sorry you found out." '
                '"I was going to eat standing up." He gave her half.' + detail +
                ' Kit put the crown beside the bread, leaving flour on its edge.')
    if scene == "ending_postponed":
        trip = ('They delivered the invitation across the lane, then returned.'
                if before["vale.location"] == "workshop" else
                'Nell gave Vale the invitation at the counter.')
        settled = ('Vale already had his working lantern and cellar oil.' if before["loan.returned"] else
                   'Vale checked the returned lantern: wick free, oil for the steps.')
        return (trip + ' ' + settled + ' Breakfast was only a question in his pocket. '
                'Kit set two cups on the counter. Nell laid the crown '
                'between them. The loaf was still unfinished; the unanswered note for the baker '
                'lay beside the empty places.')
    raise ValueError(scene)
