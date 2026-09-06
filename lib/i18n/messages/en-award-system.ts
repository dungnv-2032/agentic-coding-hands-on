import type { Dictionary } from "./dictionary";

/**
 * English Award System copy — a faithful translation of `vi-award-system.ts`,
 * not new marketing prose. Following the policy `en-home.ts` already sets:
 * design-fixed brand strings stay identical across locales — the six award
 * titles and nav labels, "ROOT FURTHER", "Sun* Annual Awards 2025", the prize
 * amounts (`7.000.000 VNĐ` is the design's currency formatting, not a number
 * to localize) and the quantities with their leading zeros.
 *
 * As in the VN file, `note` is omitted rather than set to "" for Best Manager
 * and MVP so no empty note element can render.
 */
export const enAwardSystem: Dictionary["awardSystem"] = {
  hero: {
    eyebrow: "Sun* Annual Awards 2025",
    title: "SAA 2025 Award System",
    wordmarkAlt: "ROOT FURTHER",
  },
  navAriaLabel: "Award categories",
  quantityLabel: "Number of awards:",
  prizeLabel: "Award value:",
  prizeOr: "Or",
  units: {
    individual: "Individual",
    team: "Team",
    individualOrTeam: "Individual or team",
  },
  cards: {
    topTalent: {
      title: "Top Talent",
      navLabel: "Top Talent",
      paragraphs: [
        `The Top Talent award honors individuals who excel in every dimension – people who continually prove solid professional expertise and outstanding performance, who consistently deliver value beyond expectations and are highly regarded by customers and teammates alike. Ready to take on any assignment the organization entrusts to them, they are a constant source of inspiration, driving motivation and creating a positive influence across the whole team.`,
      ],
      quantity: "10",
      prizes: [{ amount: "7.000.000 VNĐ", note: "per award" }],
    },
    topProject: {
      title: "Top Project",
      navLabel: "Top Project",
      paragraphs: [
        `The Top Project award honors outstanding project teams whose business results exceed expectations, whose operations are highly efficient and whose members work with genuine dedication. These are projects of high technical complexity that optimize resources and costs well, propose valuable ideas for the customer, deliver outstanding profit and earn positive customer feedback. Their members strictly follow internal development standards throughout the project, setting a model of excellence and professionalism.`,
      ],
      quantity: "02",
      prizes: [{ amount: "15.000.000 VNĐ", note: "per award" }],
    },
    topProjectLeader: {
      title: "Top Project Leader",
      navLabel: "Top Project Leader",
      paragraphs: [
        `The Top Project Leader award honors outstanding project managers – people who combine solid management capability, a powerful ability to inspire and the “Aim High – Be Agile” mindset in every problem and every context. Under their leadership, team members not only overcome challenges together and reach the goals they set, but also keep the fire of their enthusiasm and the Wasshoi spirit alive, growing into the finest – and happier – version of themselves.`,
      ],
      quantity: "03",
      prizes: [{ amount: "7.000.000 VNĐ", note: "per award" }],
    },
    bestManager: {
      title: "Best Manager",
      navLabel: "Best Manager",
      paragraphs: [
        `The Best Manager award honors exemplary leaders – those who have led their teams to results beyond expectations, with a standout impact on business performance and on the sustainable growth of the organization. Under their leadership, teams conquer and master every goal through versatile capability, effective collaboration and a flexible mindset for applying technology in the digital era. They inspire their teams to become confident and full of energy, ready to embrace – and even to lead – revolutionary change.`,
      ],
      quantity: "01",
      // No note — clarifications D.4 renders the amount alone.
      prizes: [{ amount: "10.000.000 VNĐ" }],
    },
    signature2025Creator: {
      title: "Signature 2025 - Creator",
      navLabel: "Signature 2025 Creator",
      paragraphs: [
        `The Signature award honors an individual or a team who embodies the distinctive spirit Sun* is striving for in a given period.`,
        `In 2025, the Signature award honors the Creator - individuals or teams with a proactive, sharp-eyed mindset, who always see opportunity in challenge and take the lead in action. They are quick to sense problems, to identify them and to put forward practical solutions that bring clear value to the project, the customer or the organization. With a creative mindset and the “Creator” spirit that is distinctly Sun*, they do not merely respond positively to change but actively create improvements, helping to shape new standards for the way Sun* people create value.`,
      ],
      quantity: "01",
      prizes: [
        { amount: "5.000.000 VNĐ", note: "for the individual award" },
        { amount: "8.000.000 VNĐ", note: "for the team award" },
      ],
    },
    mvp: {
      title: "MVP (Most Valuable Person)",
      navLabel: "MVP",
      paragraphs: [
        `The MVP award honors the most outstanding individual of the year – the representative face of the entire Sun* collective. They are the person who has shown exceptional capability, enduring dedication and far-reaching influence, leaving a strong mark on Sun*'s journey over the past year.`,
        `Beyond standing out for performance and results, they are also a source of inspiration that spreads – through their thinking, their actions and their positive influence on the collective. The MVP embodies every quality of an outstanding Sun* person and at the same time carries a great responsibility: to become the model representative of Sun*'s people and spirit, helping to lead the collective toward new heights.`,
      ],
      quantity: "01",
      // No note — clarifications D.6 renders the amount alone.
      prizes: [{ amount: "15.000.000 VNĐ" }],
    },
  },
};
