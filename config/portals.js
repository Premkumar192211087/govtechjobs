/**
 * Master list of all 59+ government portals tracked by GovTechJobs.
 * Each portal has metadata for the Portal Directory page and scraper config.
 */

const portals = [
  // ============================================================
  // IT/SOFTWARE FOCUSED PORTALS (Primary)
  // ============================================================
  {
    shortName: 'BARC',
    name: 'Bhabha Atomic Research Centre',
    url: 'https://barc.gov.in',
    category: 'it_focused',
    description: 'Premier nuclear research institute under DAE',
    itRoles: 'Scientific Officer (CS), IT Engineer',
    exams: 'OCES/DGFS, Direct Recruitment'
  },
  {
    shortName: 'BEL',
    name: 'Bharat Electronics Limited',
    url: 'https://bel-india.in',
    category: 'it_focused',
    description: 'Navratna defence electronics PSU',
    itRoles: 'Software Engineer, Project Engineer, Contract Engineer',
    exams: 'Direct Recruitment, GATE-based'
  },
  {
    shortName: 'BSNL',
    name: 'Bharat Sanchar Nigam Limited',
    url: 'https://bsnl.co.in',
    category: 'it_focused',
    description: 'Government telecom operator',
    itRoles: 'JTO (Telecom/IT), Management Trainee',
    exams: 'JTO External, MT, TTA'
  },
  {
    shortName: 'CDAC',
    name: 'Centre for Development of Advanced Computing',
    url: 'https://cdac.in',
    category: 'it_focused',
    description: 'Premier R&D organization in IT/Electronics under MeitY',
    itRoles: 'Project Engineer, Research Engineer, Software Developer',
    exams: 'Direct Recruitment, Walk-in Interviews'
  },
  {
    shortName: 'CRIS',
    name: 'Centre for Railway Information Systems',
    url: 'https://cris.org.in',
    category: 'it_focused',
    description: 'IT arm of Indian Railways',
    itRoles: 'Software Developer, System Admin, DBA',
    exams: 'Direct Recruitment'
  },
  {
    shortName: 'CSC',
    name: 'Common Services Centres',
    url: 'https://csc.gov.in',
    category: 'it_focused',
    description: 'Digital India initiative for e-governance',
    itRoles: 'IT/Digital India project roles',
    exams: 'Direct Recruitment'
  },
  {
    shortName: 'DRDO',
    name: 'Defence Research & Development Organisation',
    url: 'https://drdo.gov.in',
    category: 'it_focused',
    description: 'India\'s premier defence R&D organization',
    itRoles: 'Scientist \'B\' (CS/IT), CEPTAM Technician',
    exams: 'DRDO SET, CEPTAM, RAC'
  },
  {
    shortName: 'ECIL',
    name: 'Electronics Corporation of India Limited',
    url: 'https://ecil.co.in',
    category: 'it_focused',
    description: 'Public sector electronics company',
    itRoles: 'Graduate Engineer (CS/IT/ECE), Technical Officer',
    exams: 'GATE-based, Direct Recruitment'
  },
  {
    shortName: 'HAL',
    name: 'Hindustan Aeronautics Limited',
    url: 'https://hal-india.co.in',
    category: 'it_focused',
    description: 'India\'s largest aerospace & defence company',
    itRoles: 'Management Trainee (CS/IT), Design Engineer',
    exams: 'GATE-based MT, Direct Recruitment'
  },
  {
    shortName: 'IBPS',
    name: 'Institute of Banking Personnel Selection',
    url: 'https://ibps.in',
    category: 'it_focused',
    description: 'Common recruitment for public sector banks',
    itRoles: 'IT Officer (SO), Bank PO (IT background eligible)',
    exams: 'IBPS SO, PO, Clerk, RRB'
  },
  {
    shortName: 'ISRO',
    name: 'Indian Space Research Organisation',
    url: 'https://isro.gov.in',
    category: 'it_focused',
    description: 'India\'s space agency — world-class engineering',
    itRoles: 'Scientist/Engineer \'SC\' (CS/IT), ICRB',
    exams: 'ISRO Centralised Recruitment, ICRB'
  },
  {
    shortName: 'MTNL',
    name: 'Mahanagar Telephone Nigam Limited',
    url: 'https://mtnl.in',
    category: 'it_focused',
    description: 'Government telecom company for Delhi & Mumbai',
    itRoles: 'JTO, Management Trainee (Telecom/IT)',
    exams: 'Direct Recruitment'
  },
  {
    shortName: 'NIC',
    name: 'National Informatics Centre',
    url: 'https://nic.in',
    category: 'it_focused',
    description: 'Premier IT organization of Government of India',
    itRoles: 'Scientist B/C (CS), Technical Director',
    exams: 'NIC Scientist Exam'
  },
  {
    shortName: 'NIELIT',
    name: 'National Institute of Electronics & IT',
    url: 'https://nielit.gov.in',
    category: 'it_focused',
    description: 'IT education and training under MeitY',
    itRoles: 'Scientist, Project Engineer, Faculty',
    exams: 'Direct Recruitment, CCC Examiner'
  },
  {
    shortName: 'NTA',
    name: 'National Testing Agency',
    url: 'https://nta.ac.in',
    category: 'it_focused',
    description: 'Conducts national-level entrance/eligibility exams',
    itRoles: 'UGC NET (CS), Technical recruitment',
    exams: 'UGC NET, JEE, NEET, CUET'
  },
  {
    shortName: 'UIDAI',
    name: 'Unique Identification Authority of India',
    url: 'https://uidai.gov.in',
    category: 'it_focused',
    description: 'Aadhaar — world\'s largest biometric ID system',
    itRoles: 'IT/Tech roles for Aadhaar infrastructure',
    exams: 'Deputation, Direct Recruitment'
  },
  {
    shortName: 'STPI',
    name: 'Software Technology Parks of India',
    url: 'https://stpi.in',
    category: 'it_focused',
    description: 'Promotes IT/ITES exports from India',
    itRoles: 'Member Technical Staff, IT roles',
    exams: 'Direct Recruitment'
  },
  {
    shortName: 'MeitY',
    name: 'Ministry of Electronics & IT',
    url: 'https://meity.gov.in',
    category: 'it_focused',
    description: 'Central government IT ministry',
    itRoles: 'Digital India roles, IT policy positions',
    exams: 'Deputation, Contract'
  },
  {
    shortName: 'CERT-In',
    name: 'Indian Computer Emergency Response Team',
    url: 'https://cert-in.org.in',
    category: 'it_focused',
    description: 'National cybersecurity agency',
    itRoles: 'Cybersecurity Analyst, IT Security Specialist',
    exams: 'Deputation, Direct Recruitment'
  },
  {
    shortName: 'RailTel',
    name: 'RailTel Corporation of India',
    url: 'https://railtelindia.com',
    category: 'it_focused',
    description: 'Telecom infrastructure company under Indian Railways',
    itRoles: 'Network/System Engineer, IT Manager',
    exams: 'GATE-based, Direct Recruitment'
  },

  // ============================================================
  // MAJOR CENTRAL GOVERNMENT RECRUITMENT PORTALS
  // ============================================================
  {
    shortName: 'SSC',
    name: 'Staff Selection Commission',
    url: 'https://ssc.gov.in',
    category: 'central_govt',
    description: 'Largest recruiter for central government Group B & C posts',
    itRoles: 'Scientific Assistant, Junior Engineer, Statistical Investigator',
    exams: 'CGL, CHSL, JE, MTS, Stenographer'
  },
  {
    shortName: 'UPSC',
    name: 'Union Public Service Commission',
    url: 'https://upsc.gov.in',
    category: 'central_govt',
    description: 'Premier recruitment for Group A & B central services',
    itRoles: 'IAS/IPS (tech background), IES/ISS, CDS',
    exams: 'CSE, ESE, CDS, NDA, CAPF'
  },
  {
    shortName: 'RRB',
    name: 'Railway Recruitment Boards',
    url: 'https://rrbcdg.gov.in',
    category: 'central_govt',
    description: 'Recruitment for Indian Railways',
    itRoles: 'Junior Engineer (IT), NTPC (CS eligible)',
    exams: 'NTPC, Group D, ALP, JE, Paramedical'
  },
  {
    shortName: 'Army',
    name: 'Indian Army',
    url: 'https://joinindianarmy.nic.in',
    category: 'defence',
    description: 'Indian Army recruitment portal',
    itRoles: 'Technical Entry Scheme, SSC Tech',
    exams: 'TES, SSC Tech, NDA, CDS, Agniveer'
  },
  {
    shortName: 'Navy',
    name: 'Indian Navy',
    url: 'https://joinindiannavy.gov.in',
    category: 'defence',
    description: 'Indian Navy recruitment portal',
    itRoles: 'IT/Observer/Engineering branches',
    exams: 'SSC, PC, Agniveer, NDA'
  },
  {
    shortName: 'AirForce',
    name: 'Indian Air Force',
    url: 'https://careerindianairforce.cdac.in',
    category: 'defence',
    description: 'Indian Air Force recruitment portal',
    itRoles: 'AFCAT Technical, Cyber branch',
    exams: 'AFCAT, NDA, Agniveer'
  },
  {
    shortName: 'IndiaPost',
    name: 'India Post',
    url: 'https://indiapost.gov.in',
    category: 'central_govt',
    description: 'Postal department of India',
    itRoles: 'Postal Assistant, MTS, Postmaster',
    exams: 'GDS, PA/SA, MTS, Postmaster'
  },
  {
    shortName: 'CSIR',
    name: 'Council of Scientific & Industrial Research',
    url: 'https://csir.res.in',
    category: 'central_govt',
    description: 'Network of 38 national laboratories',
    itRoles: 'Scientist, Technical Staff at labs',
    exams: 'CSIR NET, Direct Recruitment'
  },
  {
    shortName: 'DAE',
    name: 'Department of Atomic Energy',
    url: 'https://dae.gov.in',
    category: 'central_govt',
    description: 'Nuclear energy department of India',
    itRoles: 'Scientific Officer, Technical Officer',
    exams: 'OCES/DGFS, Direct Recruitment'
  },

  // ============================================================
  // BANKING, INSURANCE & FINANCIAL
  // ============================================================
  {
    shortName: 'SBI',
    name: 'State Bank of India',
    url: 'https://sbi.co.in',
    category: 'banking',
    description: 'India\'s largest public sector bank',
    itRoles: 'IT Specialist Officer, Developer, DBA',
    exams: 'SBI PO, Clerk, SO'
  },
  {
    shortName: 'RBI',
    name: 'Reserve Bank of India',
    url: 'https://rbi.org.in',
    category: 'banking',
    description: 'India\'s central bank',
    itRoles: 'IT Officer Grade B, Security Analyst',
    exams: 'RBI Grade B, Assistant, Manager'
  },
  {
    shortName: 'NABARD',
    name: 'National Bank for Agriculture & Rural Development',
    url: 'https://nabard.org',
    category: 'banking',
    description: 'Development finance institution',
    itRoles: 'IT Officer, Manager (IT)',
    exams: 'NABARD Grade A/B, Development Assistant'
  },
  {
    shortName: 'LIC',
    name: 'Life Insurance Corporation of India',
    url: 'https://licindia.in',
    category: 'banking',
    description: 'Largest insurance company in India',
    itRoles: 'AAO, ADO (IT eligible)',
    exams: 'LIC AAO, ADO, Assistant'
  },
  {
    shortName: 'SEBI',
    name: 'Securities & Exchange Board of India',
    url: 'https://sebi.gov.in',
    category: 'banking',
    description: 'Capital markets regulator',
    itRoles: 'IT Manager, Officer Grade A (IT Stream)',
    exams: 'SEBI Grade A, IT Manager'
  },
  {
    shortName: 'SIDBI',
    name: 'Small Industries Development Bank of India',
    url: 'https://sidbi.in',
    category: 'banking',
    description: 'Development finance for MSMEs',
    itRoles: 'IT Officer',
    exams: 'SIDBI Grade A/B'
  },
  {
    shortName: 'IRDAI',
    name: 'Insurance Regulatory & Development Authority',
    url: 'https://irdai.gov.in',
    category: 'banking',
    description: 'Insurance sector regulator',
    itRoles: 'IT Manager, Assistant Director (IT)',
    exams: 'IRDAI Assistant, Manager'
  },

  // ============================================================
  // PSU / PUBLIC SECTOR UNDERTAKINGS
  // ============================================================
  {
    shortName: 'NTPC',
    name: 'National Thermal Power Corporation',
    url: 'https://ntpc.co.in',
    category: 'psu',
    description: 'India\'s largest power generating company',
    itRoles: 'Executive Trainee (IT)',
    exams: 'GATE-based ET'
  },
  {
    shortName: 'ONGC',
    name: 'Oil & Natural Gas Corporation',
    url: 'https://ongcindia.com',
    category: 'psu',
    description: 'Maharatna oil and gas company',
    itRoles: 'AEE (IT), Graduate Trainee',
    exams: 'GATE-based GT, Direct Recruitment'
  },
  {
    shortName: 'IOCL',
    name: 'Indian Oil Corporation Limited',
    url: 'https://iocl.com',
    category: 'psu',
    description: 'India\'s largest oil company by revenue',
    itRoles: 'Engineers/Officers (IT/CS)',
    exams: 'GATE-based, Apprentice'
  },
  {
    shortName: 'GAIL',
    name: 'Gas Authority of India Limited',
    url: 'https://gailonline.com',
    category: 'psu',
    description: 'India\'s largest natural gas company',
    itRoles: 'Executive Trainee (IT)',
    exams: 'GATE-based ET'
  },
  {
    shortName: 'BHEL',
    name: 'Bharat Heavy Electricals Limited',
    url: 'https://bhel.com',
    category: 'psu',
    description: 'Largest engineering & manufacturing PSU',
    itRoles: 'Engineer Trainee (Electronics/CS)',
    exams: 'GATE-based ET'
  },
  {
    shortName: 'PowerGrid',
    name: 'Power Grid Corporation of India',
    url: 'https://powergrid.in',
    category: 'psu',
    description: 'Central transmission utility of India',
    itRoles: 'Executive Trainee (IT/CS)',
    exams: 'GATE-based ET'
  },
  {
    shortName: 'CoalIndia',
    name: 'Coal India Limited',
    url: 'https://coalindia.in',
    category: 'psu',
    description: 'World\'s largest coal producing company',
    itRoles: 'Management Trainee (System/IT)',
    exams: 'GATE-based MT'
  },
  {
    shortName: 'SAIL',
    name: 'Steel Authority of India Limited',
    url: 'https://sail.co.in',
    category: 'psu',
    description: 'India\'s largest steel making PSU',
    itRoles: 'Management Trainee (CS/IT)',
    exams: 'GATE-based MT'
  },
  {
    shortName: 'HPCL',
    name: 'Hindustan Petroleum Corporation Limited',
    url: 'https://hindustanpetroleum.com',
    category: 'psu',
    description: 'Maharatna oil refining & marketing company',
    itRoles: 'Officer (IT/CS)',
    exams: 'GATE-based, Direct Recruitment'
  },
  {
    shortName: 'BPCL',
    name: 'Bharat Petroleum Corporation Limited',
    url: 'https://bharatpetroleum.in',
    category: 'psu',
    description: 'Maharatna petroleum company',
    itRoles: 'Management Trainee (IT)',
    exams: 'GATE-based MT'
  },
  {
    shortName: 'CONCOR',
    name: 'Container Corporation of India',
    url: 'https://concorindia.co.in',
    category: 'psu',
    description: 'Container transport and logistics PSU',
    itRoles: 'Management roles',
    exams: 'Direct Recruitment'
  },
  {
    shortName: 'NPCIL',
    name: 'Nuclear Power Corporation of India',
    url: 'https://npcil.nic.in',
    category: 'psu',
    description: 'Operates nuclear power plants in India',
    itRoles: 'Scientific Officer, Engineer (CS/IT)',
    exams: 'GATE-based, Direct Recruitment'
  },
  {
    shortName: 'NHPC',
    name: 'National Hydroelectric Power Corporation',
    url: 'https://nhpcindia.com',
    category: 'psu',
    description: 'Hydroelectric power generation PSU',
    itRoles: 'Trainee Engineer (IT)',
    exams: 'GATE-based TE'
  },
  {
    shortName: 'THDC',
    name: 'THDC India Limited',
    url: 'https://thdc.co.in',
    category: 'psu',
    description: 'Hydropower and renewable energy PSU',
    itRoles: 'Executive Trainee',
    exams: 'GATE-based ET'
  },

  // ============================================================
  // EDUCATION & RESEARCH
  // ============================================================
  {
    shortName: 'IITs',
    name: 'Indian Institutes of Technology',
    url: 'https://iit.ac.in',
    category: 'education',
    description: 'Premier engineering institutes (23 IITs)',
    itRoles: 'Faculty, Technical Staff, System Admin',
    exams: 'Direct Recruitment, Walk-in'
  },
  {
    shortName: 'NITs',
    name: 'National Institutes of Technology',
    url: 'https://nitcouncil.org.in',
    category: 'education',
    description: 'Technical institutes of national importance (31 NITs)',
    itRoles: 'Faculty, Lab staff, Technical Assistants',
    exams: 'Direct Recruitment'
  },
  {
    shortName: 'AIIMS',
    name: 'All India Institute of Medical Sciences',
    url: 'https://aiimsexams.ac.in',
    category: 'education',
    description: 'Premier medical research institutes',
    itRoles: 'IT/System staff, Data Entry Operator',
    exams: 'Direct Recruitment, Nursing, Faculty'
  },
  {
    shortName: 'KVS',
    name: 'Kendriya Vidyalaya Sangathan',
    url: 'https://kvsangathan.nic.in',
    category: 'education',
    description: 'Central government school system (1,200+ schools)',
    itRoles: 'PGT Computer Science, Computer Instructor',
    exams: 'KVS TGT/PGT, Principal'
  },
  {
    shortName: 'NVS',
    name: 'Navodaya Vidyalaya Samiti',
    url: 'https://navodaya.gov.in',
    category: 'education',
    description: 'Residential schools for talented rural students',
    itRoles: 'PGT Computer Science, Computer Instructor',
    exams: 'NVS TGT/PGT, Principal'
  },
  {
    shortName: 'UGC',
    name: 'University Grants Commission',
    url: 'https://ugc.gov.in',
    category: 'education',
    description: 'Regulates and funds higher education',
    itRoles: 'NET qualified positions, Assistant Professor (CS)',
    exams: 'UGC NET, Faculty Positions'
  },

  // ============================================================
  // STATE GOVERNMENT & SMART CITY
  // ============================================================
  {
    shortName: 'StatePSC',
    name: 'State Public Service Commissions',
    url: 'https://upsc.gov.in/state-pscs',
    category: 'state',
    description: 'UPPSC, MPPSC, RPSC, TNPSC, KPSC, APPSC, TSPSC & more',
    itRoles: 'State IT officers, Technical Assistants',
    exams: 'State PCS, Various'
  },
  {
    shortName: 'StateIT',
    name: 'State IT Departments',
    url: 'https://meity.gov.in/state-it',
    category: 'state',
    description: 'Various state e-governance portals',
    itRoles: 'IT Officers, e-Governance roles',
    exams: 'State-specific recruitment'
  },
  {
    shortName: 'SmartCity',
    name: 'Smart Cities Mission',
    url: 'https://smartcities.gov.in',
    category: 'state',
    description: 'Urban transformation initiative with IT/Project roles',
    itRoles: 'IT Project Manager, Smart City Fellow, Data Analyst',
    exams: 'Contract/Fellowship based'
  }
];

/**
 * Get portals by category
 */
function getPortalsByCategory(category) {
  return portals.filter(p => p.category === category);
}

/**
 * Get a portal by its short name
 */
function getPortalByShortName(shortName) {
  return portals.find(p => p.shortName.toLowerCase() === shortName.toLowerCase());
}

/**
 * Get all unique categories
 */
function getCategories() {
  return [...new Set(portals.map(p => p.category))];
}

const categoryLabels = {
  it_focused: '🖥️ IT/Software Focused',
  central_govt: '🏛️ Central Government',
  defence: '🎖️ Defence',
  banking: '🏦 Banking & Finance',
  psu: '⚡ PSU',
  education: '🎓 Education & Research',
  state: '🗺️ State Government'
};

module.exports = { portals, getPortalsByCategory, getPortalByShortName, getCategories, categoryLabels };
