// ==================== SISTEMA DE INTERNACIONALIZAÇÃO (i18n) ====================

// Mapeamento de tradução de nomes de equipas (de PT para EN)
const teamNamesTranslation = {
    'pt': {
        'Administração Pública': 'Public Administration',
        'AP': 'PA',
        'Aero': 'Aero',
        'Automação e Sistemas de Produção': 'Automation and Production Systems',
        'ASP': 'APS',
        'Biologia': 'Biology',
        'Biologia e Geologia': 'Biology and Geology',
        'BG': 'BG',
        'Bioquímica': 'Biochemistry',
        'Biotec': 'Biotech',
        'Biotecnologia': 'Biotechnology',
        'Ciências Biomédicas': 'Biomedical Sciences',
        'Ciências Biomédicas B': 'Biomedical Sciences B',
        'Bimédica': 'Biomedical',
        'Biomédica': 'Biomedical',
        'CBM': 'BMS',
        'CBM B': 'BMS B',
        'Ciências do Mar': 'Marine Sciences',
        'CM': 'MS',
        'Contabilidade': 'Accounting',
        'Contab': 'Accounting',
        'Civil': 'Civil',
        'Computacional': 'Computational',
        'EAmb': 'Env',
        'EB': 'BE',
        'Design': 'Design',
        'Design de Produto e Tecnologia': 'Product Design and Technology',
        'DPT': 'PDT',
        'Economia': 'Economics',
        'Educação Básica': 'Basic Education',
        'Enfermagem': 'Nursing',
        'Eng. Aeroespacial': 'Aeronautical Engineering',
        'Eng. Biomédica': 'Biomedical Engineering',
        'Eng. Civil': 'Civil Engineering',
        'Eng. Computacional': 'Computational Engineering',
        'Eng. Computadores e Telemática': 'Computers and Telematics Engineering',
        'ECT': 'CTE',
        'Eng. de Materiais': 'Materials Engineering',
        'Materiais': 'Materials',
        'Eng. do Ambiente': 'Environmental Engineering',
        'Eng. e Gestão Industrial': 'Industrial Engineering and Management',
        'Eng. e Gestão Industrial B': 'Industrial Engineering and Management B',
        'EGI': 'IEM',
        'EGI B': 'IEM B',
        'Eng. Eletrónica e Telecomunicações': 'Electronics and Telecommunications Engineering',
        'Eng. Eletrónica e Telecomunicações B': 'Electronics and Telecommunications Engineering B',
        'EET': 'ETE',
        'EET B': 'ETE B',
        'Eng. Física': 'Physics Engineering',
        'EF': 'PE',
        'Eng. Informática': 'Computer Science and Engineering',
        'Eng. Informática B': 'Computer Science and Engineering B',
        'EI': 'CSE',
        'EI B': 'CSE B',
        'Eng. Mecânica': 'Mechanical Engineering',
        'Eng. Mecânica B': 'Mechanical Engineering B',
        'Mecânica': 'Mechanical',
        'Mecânica B': 'Mechanical B',
        'Eng. Química': 'Chemical Engineering',
        'EQ': 'CE',
        'Estudos Editoriais': 'Editorial Studies',
        'Finanças': 'Finance',
        'Física': 'Physics',
        'Fisioterapia': 'Physiotherapy',
        'Geologia': 'Geology',
        'Gestão': 'Management',
        'Gestão Comercial': 'Business Management',
        'Gest. Comercial': 'Business Mgmt',
        'Gestão e Planeamento em Turismo': 'Tourism Management and Planning',
        'GPT': 'TMP',
        'Gestão Pública': 'Public Management',
        'Gest. Pública': 'Public Mgmt',
        'Línguas e Relações Empresariais': 'Languages and Business Relations',
        'LRE': 'LBR',
        'Línguas, Literaturas e Culturas': 'Languages, Literatures and Cultures',
        'LLC': 'LLC',
        'Marketing': 'Marketing',
        'Matemática': 'Mathematics',
        'Medicina': 'Medicine',
        'Meteorologia, Oceanografia e Clima': 'Meteorology, Oceanography and Climate',
        'MOC': 'MOC',
        'MTC': 'MCT',
        'Música': 'Music',
        'Multimédia e Tecnologias da Comunicação': 'Multimedia and Communication Technologies',
        'Psicologia': 'Psychology',
        'Química': 'Chemistry',
        'Tecnologias de Informação': 'Information Technologies',
        'TI': 'IT',
        'Terapia da Fala': 'Speech-Language Pathology',
        'Tradução': 'Translation'
    }
};

teamNamesTranslation.en = { ...teamNamesTranslation.pt };
teamNamesTranslation.es = {
    'Administração Pública': 'Administración Pública',
    'AP': 'AP',
    'Aero': 'Aero',
    'Automação e Sistemas de Produção': 'Automatización y Sistemas de Producción',
    'ASP': 'ASP',
    'Biologia': 'Biología',
    'Biologia e Geologia': 'Biología y Geología',
    'BG': 'BG',
    'Bioquímica': 'Bioquímica',
    'Biotec': 'Biotec',
    'Biotecnologia': 'Biotecnología',
    'Ciências Biomédicas': 'Ciencias Biomédicas',
    'Ciências Biomédicas B': 'Ciencias Biomédicas B',
    'Bimédica': 'Biomédica',
    'Biomédica': 'Biomédica',
    'CBM': 'CBM',
    'CBM B': 'CBM B',
    'Ciências do Mar': 'Ciencias del Mar',
    'CM': 'CM',
    'Contabilidade': 'Contabilidad',
    'Contab': 'Contab',
    'Civil': 'Civil',
    'Computacional': 'Computacional',
    'EAmb': 'IAmb',
    'EB': 'EB',
    'Design': 'Diseño',
    'Design de Produto e Tecnologia': 'Diseño de Producto y Tecnología',
    'DPT': 'DPT',
    'Economia': 'Economía',
    'Educação Básica': 'Educación Básica',
    'Enfermagem': 'Enfermería',
    'Eng. Aeroespacial': 'Ing. Aeroespacial',
    'Eng. Biomédica': 'Ing. Biomédica',
    'Eng. Civil': 'Ing. Civil',
    'Eng. Computacional': 'Ing. Computacional',
    'Eng. Computadores e Telemática': 'Ing. Computadores y Telemática',
    'ECT': 'ICT',
    'Eng. de Materiais': 'Ing. de Materiales',
    'Materiais': 'Materiales',
    'Eng. do Ambiente': 'Ing. del Ambiente',
    'Eng. e Gestão Industrial': 'Ing. y Gestión Industrial',
    'Eng. e Gestão Industrial B': 'Ing. y Gestión Industrial B',
    'EGI': 'IGI',
    'EGI B': 'IGI B',
    'Eng. Eletrónica e Telecomunicações': 'Ing. Electrónica y Telecomunicaciones',
    'Eng. Eletrónica e Telecomunicações B': 'Ing. Electrónica y Telecomunicaciones B',
    'EET': 'IET',
    'EET B': 'IET B',
    'Eng. Física': 'Ing. Física',
    'EF': 'IF',
    'Eng. Informática': 'Ing. Informática',
    'Eng. Informática B': 'Ing. Informática B',
    'EI': 'II',
    'EI B': 'II B',
    'Eng. Mecânica': 'Ing. Mecánica',
    'Eng. Mecânica B': 'Ing. Mecánica B',
    'Mecânica': 'Mecánica',
    'Mecânica B': 'Mecánica B',
    'Eng. Química': 'Ing. Química',
    'EQ': 'IQ',
    'Estudos Editoriais': 'Estudios Editoriales',
    'Finanças': 'Finanzas',
    'Física': 'Física',
    'Fisioterapia': 'Fisioterapia',
    'Geologia': 'Geología',
    'Gestão': 'Gestión',
    'Gestão Comercial': 'Gestión Comercial',
    'Gest. Comercial': 'Gest. Comercial',
    'Gestão e Planeamento em Turismo': 'Gestión y Planificación en Turismo',
    'GPT': 'GPT',
    'Gestão Pública': 'Gestión Pública',
    'Gest. Pública': 'Gest. Pública',
    'Línguas e Relações Empresariais': 'Lenguas y Relaciones Empresariales',
    'LRE': 'LRE',
    'Línguas, Literaturas e Culturas': 'Lenguas, Literaturas y Culturas',
    'LLC': 'LLC',
    'Marketing': 'Marketing',
    'Matemática': 'Matemáticas',
    'Medicina': 'Medicina',
    'Meteorologia, Oceanografia e Clima': 'Meteorología, Oceanografía y Clima',
    'MOC': 'MOC',
    'MTC': 'MTC',
    'Música': 'Música',
    'Multimédia e Tecnologias da Comunicação': 'Multimedia y Tecnologías de la Comunicación',
    'Psicologia': 'Psicología',
    'Química': 'Química',
    'Tecnologias de Informação': 'Tecnologías de la Información',
    'TI': 'TI',
    'Terapia da Fala': 'Terapia del Habla',
    'Tradução': 'Traducción'
};

const translations = {
    pt: {
        // === Página / Meta ===
        pageTitle: 'Dashboard da Taça UA',
        pageDescription: 'Dashboard interativo da Taça UA - Rankings, estatísticas ELO, calendário de jogos e brackets de eliminação',

        // === Header ===
        dashboardTitle: 'Dashboard da Taça UA',

        // === Seletores ===
        seasonLabel: 'Época:',
        modalityLabel: 'Modalidade:',

        // === Classificação ===
        generalRanking: 'Classificação Geral',
        compactMode: 'Modo Compacto',
        posTitle: 'Posição na classificação geral',
        posAbbr: 'Pos.',
        team: 'Equipa',
        ptsTitle: 'Pontos acumulados',
        ptsAbbr: 'Pts',
        gamesTitle: 'Jogos realizados',
        gamesAbbr: 'GP',
        winsTitle: 'Vitórias',
        winsAbbr: 'V',
        drawsTitle: 'Empates',
        drawsAbbr: 'E',
        lossesTitle: 'Derrotas',
        lossesAbbr: 'D',
        noShowsTitle: 'Faltas de comparência',
        noShowsAbbr: 'FF',
        goalDiffSymbol: '±',
        eloTrend: 'ELO Trend',
        eloTrendTitle: 'Mostra a evolução do rating ELO da equipa nos 5 jogos mais recentes.\nELO minimo - ELO máximo',
        form: 'Forma',
        formTitle: 'Mostra os últimos 5 resultados da equipa (V=Vitória, E=Empate, D=Derrota)\nEsquerda é o jogo mais antigo, direita o mais recente.',
        noDataAvailable: 'Nenhum dado disponível',
        selectModality: 'Selecione uma modalidade',
        selectModalityData: 'Selecione uma modalidade para ver os dados',
        selectModalityBracket: 'Selecione uma modalidade para ver o bracket',
        selectModalityFirst: 'Selecione uma modalidade primeiro',
        removeFavorite: 'Remover dos favoritos',
        markFavorite: 'Marcar como favorita',
        favoriteRemoved: 'Equipa favorita removida',
        favoriteSet: 'Equipa favorita:',
        eloCurrentTitle: 'ELO atual e posição no ranking geral',
        unknownDate: 'Data desconhecida',
        lastGame: 'último jogo',

        // === Dias da Semana ===
        weekdayShortSun: 'Dom',
        weekdayShortMon: 'Seg',
        weekdayShortTue: 'Ter',
        weekdayShortWed: 'Qua',
        weekdayShortThu: 'Qui',
        weekdayShortFri: 'Sex',
        weekdayShortSat: 'Sáb',

        form: 'Forma',
        placeLabel: 'lugar',

        // === Forma (V/E/D) ===
        formWin: 'Vitória',
        formDraw: 'Empate',
        formLoss: 'Derrota',
        formUnknown: 'Desconhecido',
        formWinLetter: 'V',
        formDrawLetter: 'E',
        formLossLetter: 'D',

        // === ELO Sparkline ===
        eloEvolution: 'Evolução de ELO',
        lastGames: 'jogos',
        until: 'até',
        eloTrendAriaLabel: 'Tendência de ELO',

        // === Gráfico ELO ===
        eloChartTitle: 'Evolução de ELO das Equipas',
        eloQuickViews: 'Vistas rápidas',
        eloTeamsInChart: 'Equipas no gráfico',
        eloChartTooltip: 'ELO representa a força relativa das equipas ao longo da época. Sobe com vitórias, desce com derrotas.',
        expandCollapse: 'Expandir/Colapsar',
        previousSeason: '← Época Anterior',
        nextSeason: 'Época Seguinte →',
        teamsLabel: 'equipas',

        // === Seletor de equipas ===
        selectAll: 'Seleccionar Todas',
        deselectAll: 'Desseleccionar Todas',
        invertSelection: 'Inverter Seleção',
        selectAllAria: 'Selecionar todas as equipas',
        deselectAllAria: 'Desselecionar todas as equipas',
        invertSelectionAria: 'Inverter seleção de equipas',
        allGroups: 'Todos',
        divisionGeneral: 'Divisão Geral',
        divisionNth: 'ª Divisão',
        teamSingular: 'equipa',
        teamPlural: 'equipas',
        groupLabel: 'Grupo',

        // === Filtros rápidos ===
        filterTop3: 'Top 3',
        filterTop3Aria: 'Filtrar top 3 equipas',
        filterByLabel: 'Filtrar por',
        filterByAllDiv2: 'Filtrar por toda a 2ª Divisão',
        playoffsLabel: 'Playoffs',
        playoffsCurrentRanking: 'Playoffs (Classificação Atual)',
        filterPlayoffsAria: 'Filtrar equipas dos playoffs',
        sensationTeams: 'Equipas Sensação',
        sensationTeamsAria: 'Filtrar equipas sensação com maior ganho de ELO',
        resetFilter: 'Resetar Filtro',
        resetFilterAria: 'Resetar filtros de equipas',

        // === Calendário ===
        gameCalendar: 'Calendário de Jogos',
        calendarSortAria: 'Ordenação do calendário',
        calendarSortDateTime: 'Por Data/Hora',
        calendarSortMatchday: 'Por Jornada',
        calendarSortTeam: 'Por Equipa',
        matchday: 'Jornada',
        calendarDateLabel: 'Data',
        calendarTeamPagePrefix: 'Equipa',
        selectMatchday: 'Selecione uma jornada para ver os jogos',
        noGamesFound: 'Nenhum jogo encontrado para esta jornada',
        noGamesFoundDateMode: 'Nenhum jogo encontrado para esta data',
        noGamesFoundTeamMode: 'Nenhum jogo encontrado para esta equipa',
        noGamesAvailable: 'Sem jogos disponíveis',
        noMatchdaysAvailable: 'Sem jornadas disponíveis',
        calendarNoDatePage: 'Sem data marcada',
        dateToSchedule: 'DATA POR MARCAR',
        previousMatchday: 'Jornada anterior',
        nextMatchday: 'Jornada seguinte',
        navigatePrevious: 'Navegar para jornada anterior',
        navigateNext: 'Navegar para próxima jornada',

        // === Brackets ===
        eliminationBracket: 'Bracket de Eliminação',
        playoffScenariosTitle: 'Cenários de Playoff e Finais',
        playoffLiguilha: 'Playoff/Liguilha',
        secondaryBracketTitle: 'Manutenção/Liguilha',
        maintenanceLiguillaScenariosTitle: 'Cenários de Promoção/Manutenção',
        maintenanceFirstPhase: '1ºFase',
        maintenanceFinalPhase: 'Fase final',
        liguilhaRound1: 'Liguilha 1',
        liguilhaRound2: 'Liguilha 2',
        bracketNotAvailable: 'Bracket não disponível para esta modalidade',
        thirdPlace: '3º Lugar',
        bracketLabel1stDivision: '1ª Divisão',
        bracketLabel2ndDivision: '2ª Divisão',
        bracketLabelLeague: 'da Liga',
        bracketLabelGroup: 'Grupo',
        bracketQualificationSuffix: 'º',
        bracketWinner: 'Vencedor',
        bracketLoser: 'Perdedor',
        fourthPlace: '4º Lugar',
        predictedMatch: '📅 Confronto Previsto',
        unknownResult: '⚠️ Resultado Desconhecido',
        calendarPendingResultWarning: 'Resultado por afixar / Jogo adiado',
        quarterFinals: 'Quartos de Final',
        semiFinals: 'Meias-Finais',
        finals: 'Final',
        ofTheLeague: 'da Liga',
        div1st: '1st Div',
        div2nd: '2nd Div',
        groupAbbr: 'Gr.',

        // === Legenda de progressão ===
        playoffs: 'Play-offs',
        maintenancePlayoff: 'Play-off de Manutenção',
        maintenanceLeague: 'Liguilha de Manutenção',
        relegation: 'Descida de divisão',
        playoffsPromotion: 'Play-offs + Promoção',
        promotionPlayoff: 'Play-off de Promoção',
        promotionLeague: 'Liguilha de Promoção',
        promotion: 'Subida de divisão',
        safeZone: 'Zona segura',
        qualificationPlayoffs: 'Qualificação para play-offs',
        replaces: 'substitui',
        ofGroup: 'do grupo',
        teamBNoQualify: 'equipa B não qualifica',
        tiebreakIndicatorAria: 'Indicador de desempate',
        tiebreakApplied: 'Desempate aplicado',
        tiebreakMiniLeague: 'Miniliga',
        tiebreakHeadToHead: 'Confronto direto',
        tiebreakTiePoints: 'Pontos em empate',
        tiebreakTiedTeams: 'Equipas empatadas',
        tiebreakCriteriaOrder: 'Ordem de critérios',
        tiebreakDecidingCriterion: 'Critério decisivo',
        tiebreakAppliedByPosition: 'Critérios aplicados por posição',
        tiebreakFallback: 'Fallback global',
        tiebreakFallbackYes: 'Sim',
        tiebreakFallbackNo: 'Não',
        tiebreakTeamValues: 'Valores da equipa',
        tbFaltasComparencia: 'Faltas de Comparência',
        tbPointsH2H: 'Pontos (h2h)',
        tbNoShowsH2H: 'Faltas (h2h)',
        tbSetDiffH2H: 'Diferença de sets (h2h)',
        tbScoreDiffH2H: 'Diferença de score (h2h)',
        tbScoreScoredH2H: 'Score marcado (h2h)',
        tbBasketDiffH2H: 'Diferença de cestos (h2h)',
        tbBasketsScoredH2H: 'Cestos marcados (h2h)',
        tbSetsScoredH2H: 'Sets ganhos (h2h)',
        tbGoalDiffH2H: 'Diferença de golos (h2h)',
        tbGoalsScoredH2H: 'Golos marcados (h2h)',
        tbSetDiffOverall: 'Diferença de sets (geral)',
        tbScoreDiffOverall: 'Diferença de score (geral)',
        tbScoreScoredOverall: 'Score marcado (geral)',
        tbBasketDiffOverall: 'Diferença de cestos (geral)',
        tbBasketsScoredOverall: 'Cestos marcados (geral)',
        tbSetsScoredOverall: 'Sets ganhos (geral)',
        tbGoalDiffOverall: 'Diferença de golos (geral)',
        tbGoalsScoredOverall: 'Golos marcados (geral)',

        // === Previsões ===
        seasonPredictions: 'Previsões da Época',
        teamDetailsTitle: 'Detalhes das Equipas',
        generalPredictions: 'PREVISÕES GERAIS',
        teamSeasonOverview: 'Previsões da Época',
        matchdayPredictions: 'Previsões jornada a jornada',
        teamMatchHistory: 'Histórico de Jogos',
        predJornada: 'Jornada',
        predDate: 'Data',
        predOpponent: 'Adversário',
        predWinProb: 'P(V)',
        predWinProbTitle: 'Probabilidade de vitória',
        predDrawProb: 'P(E)',
        predDrawProbTitle: 'Probabilidade de empate',
        predLossProb: 'P(D)',
        predLossProbTitle: 'Probabilidade de derrota',
        expectedGoals: 'Golos Esp.',
        expectedGoalsAbbr: 'Golos Esp.',
        expectedGoalsTitle: 'Golos esperados',
        basketGoalsExpected: 'Pontos Esp.',
        basketGoalsTitle: 'Pontos esperados',
        setsExpected: 'Sets Esp.',
        setsTitle: 'Sets esperados',
        noStatsAvailable: 'Sem estatísticas disponíveis',
        noPredictionsData: 'Sem dados de previsões para esta modalidade/época',
        noDataAvailableShort: 'Sem dados disponíveis',
        errorLoading: 'Erro ao carregar',
        loading: 'A carregar',
        showMore: 'Ver mais',
        loadingData: 'A carregar dados...',
        loadingRankings: 'A carregar classificação...',
        noGamesForTeam: 'Sem jogos previstos para esta equipa',
        noHistoryForTeam: 'Sem jogos disponíveis para esta equipa',
        dataNotAvailable: 'Dados não disponíveis',
        simulations: 'simulações',
        simulatedResults: 'Resultados Simulados',
        eloDeltaLabel: 'Delta ELO',
        clickToFixTooltip: 'Clique para fixar/desafixar o tooltip de distribuição',
        previousTeam: 'Equipa anterior',
        nextTeam: 'Próxima equipa',
        teamCarouselAria: 'Selecionar equipa nos detalhes',
        teamCarouselHint: 'Desliza ou toca numa equipa',
        seasonStart: 'Início da Época',
        eloFinalPreviousSeason: 'ELO Final Época Anterior',
        eloSeasonStart: 'ELO Início da Época',
        interGroupAdjustments: 'Ajustes Inter-Grupos',
        eloRatingLabel: 'Rating ELO',

        // Cabeçalhos dinâmicos por modalidade
        basketScored: 'Cestos feitos',
        basketConceded: 'Cestos sofridos',
        basketDiff: 'Diferença de cestos (CF - CS)',
        setsWon: 'Sets ganhos',
        setsLost: 'Sets perdidos',
        setsDiff: 'Diferença de sets (SG - SP)',
        goalsScored: 'Golos marcados',
        goalsConceded: 'Golos sofridos',
        goalsDiff: 'Diferença de golos (GM - GS)',

        // Estatísticas de previsão
        predPlayoffs: 'Playoffs',
        predSemiFinals: 'Meias-Finais',
        predFinal: 'Final',
        predChampionsMale: 'Campeões',
        predChampionsFemale: 'Campeãs',
        predChampionsMaleDesc: 'Probabilidade de serem campeões',
        predChampionsFemaleDesc: 'Probabilidade de serem campeãs',
        predQualification: 'Probabilidade de qualificação',
        predReachSemis: 'Probabilidade de chegarem às meias',
        predReachFinals: 'Probabilidade de chegarem à final',
        expectedPoints: 'Pontos Esperados',
        expectedPosition: 'Posição Esperada no Grupo',
        expectedValue: 'Valor esperado',
        positions: 'posições',
        points: 'pontos',
        avgFinalElo: 'ELO Final Médio',
        predPromotion: 'Promoção',
        predPromotionDesc: 'Probabilidade de subir de divisão',
        predRelegation: 'Descida',
        predRelegationDesc: 'Probabilidade de descer de divisão',
        predLiguillaLm1Play: 'Disputa LM1',
        predLiguillaLm1PlayDesc: 'Probabilidade de disputar a Liguilha 1',
        predLiguillaLm1WinCond: 'Ganha LM1 (cond.)',
        predLiguillaLm1WinCondDesc: 'Probabilidade de ganhar LM1, dado que disputa LM1',
        predLiguillaLm2PlayCond: 'Disputa LM2 (cond.)',
        predLiguillaLm2PlayCondDesc: 'Probabilidade de disputar LM2, dado que disputa LM1',
        predLiguillaLm2WinCond: 'Ganha LM2 (cond.)',
        predLiguillaLm2WinCondDesc: 'Probabilidade de ganhar LM2, dado que disputa LM2',
        predLiguillaLm3PlayCond: 'Disputa LM3 (cond.)',
        predLiguillaLm3PlayCondDesc: 'Probabilidade de disputar LM3, dado que disputa LM2',
        predLiguillaLm3WinCond: 'Ganha LM3 (cond.)',
        predLiguillaLm3WinCondDesc: 'Probabilidade de ganhar LM3, dado que disputa LM3',
        predLiguillaPromotion: 'Promoção via Liguilha',
        predLiguillaPromotionDesc: 'Probabilidade total de promoção via LM1-LM3',
        liguillaScenariosGroupedTitle: 'Cenários Agrupados da Liguilha',
        scenarioLabel: 'Cenário',
        scenarioProbability: 'Probabilidade do cenário',
        scenarioPassProbability: 'Probabilidade de passar no cenário',
        scenarioStayProbability: 'Probabilidade de permanecer na 1ª Divisão neste cenário',
        scenarioPromotionProbability: 'Probabilidade de subir neste cenário',
        unknown: 'Desconhecido',

        // === Tooltip Histórico ===
        historicalRankings: 'Histórico de Classificações',
        season: 'Época',
        group: 'Grupo',
        general: 'Geral',
        inProgress: 'em andamento',
        didNotParticipate: 'Não participou',
        as: 'Como',

        // === Golos/Cestos/Sets (sport-specific) ===
        goalsScored: 'Golos marcados',
        goalsConceded: 'Golos sofridos',
        goalsDiff: 'Diferença de golos (GM - GS)',
        goalsExpected: 'Golos esperados',
        goalsScoredAbbr: 'GF',
        goalsConcededAbbr: 'GA',
        goalsExpectedAbbr: 'Expected Goals',
        basketsScored: 'Cestos feitos',
        basketsConceded: 'Cestos sofridos',
        basketsDiff: 'Diferença de cestos (CF - CS)',
        basketsExpected: 'Pontos esperados',
        basketsScoredAbbr: 'BS',
        basketsConcededAbbr: 'BC',
        basketsExpectedAbbr: 'Expected Points',
        setsWon: 'Sets ganhos',
        setsLost: 'Sets perdidos',
        setsDiff: 'Diferença de sets (SG - SP)',
        setsExpected: 'Sets esperados',
        setsWonAbbr: 'SW',
        setsLostAbbr: 'SL',
        setsExpectedAbbr: 'Expected Sets',

        // === Campeões === 
        championsMale: 'Campeões',
        championsViceMale: 'Vice-Campeões',
        championsFemale: 'Campeãs',
        championsViceFemale: 'Vice-Campeãs',

        // === DivisionSelector ===
        div1Label: '1ª Divisão',
        div2Label: '2ª Divisão',

        // === Modalidades ===
        ANDEBOL_MISTO: 'Andebol Misto',
        BASQUETEBOL_FEMININO: 'Basquetebol Feminino',
        BASQUETEBOL_MASCULINO: 'Basquetebol Masculino',
        FUTEBOL_DE_7_MASCULINO: 'Futebol 7 Masculino',
        FUTSAL_FEMININO: 'Futsal Feminino',
        FUTSAL_MASCULINO: 'Futsal Masculino',
        VOLEIBOL_FEMININO: 'Voleibol Feminino',
        VOLEIBOL_MASCULINO: 'Voleibol Masculino',

        // === Termos de Divisão/Grupo ===
        division: 'Divisão',
        group: 'Grupo',
        divisionLabel: 'ª Divisão',
        mainDivision: '1ª Divisão',
        secondDivision: '2ª Divisão',
        groupA: 'Grupo A',
        groupB: 'Grupo B',
        groupC: 'Grupo C',
        groupD: 'Grupo D',

        // === Termos Adicionais ===
        selectAllTeams: 'Seleccionar Todas',
        deselectAllTeams: 'Desseleccionar Todas',
        invertSelection: 'Inverter Seleção',
        teams: 'equipas',
        team: 'equipa',
        thirdPlace: '3º Lugar',
        fourthPlace: '4º Lugar',
        groupPrefix: 'Grupo ',
        divisionPrefix: 'ª Divisão',
        noMatchesAvailable: 'Nenhum jogo disponível',
        roundOf: 'Ronda de ',
        vs: 'vs',
        home: 'Casa',
        away: 'Fora',
        draw: 'Empate',
        matchday: 'Jornada',
        date: 'Data',
        time: 'Hora',
        location: 'Local',
        locationToSchedule: 'LOCAL POR MARCAR',
        provisionalDatePlaceholder: 'Data provisória - aguarda confirmação',
        provisionalLocationPlaceholder: 'Local provisório - aguarda confirmação',
        opponent: 'Adversário',
        result: 'Resultado',
        score: 'Pontuação',

        // === Rótulos de Rodadas (para use em rótulos curtos) ===
        roundQuarters: 'Quartos',
        roundSemiFinals: 'Meias',
        roundFinal: 'Final',
        eloFinal: 'ELO final',
        previousSeason: 'Época Anterior',
        nextSeason: 'Época Seguinte',

        // === Navbar ===
        navRankings: 'Rankings',
        navElo: 'ELO',
        navCalendar: 'Calendário',
        navBracket: 'Bracket',
        navPredictions: 'Detalhes',

        // === Footer ===
        footerMadeBy: 'Projeto criado por Fábio Matias',
        footerDisclaimer: 'Este projeto não está oficialmente associado à AAUAv e pode conter imprecisões',
        footerRepositoryAndDocs: 'Repositório e documentação',
        footerResourcesLabel: 'Repositório e documentação:',
        footerRepository: 'Repositório',
        footerDocumentation: 'Documentação',
    },

    en: {
        // === Page / Meta ===
        pageTitle: 'UA Cup Dashboard',
        pageDescription: 'Interactive UA Cup Dashboard - Rankings, ELO statistics, match schedule and elimination brackets',

        // === Header ===
        dashboardTitle: 'UA Cup Dashboard',

        // === Selectors ===
        seasonLabel: 'Season:',
        modalityLabel: 'Sport:',

        // === Rankings ===
        generalRanking: 'General Standings',
        compactMode: 'Compact Mode',
        posTitle: 'Position in general standings',
        posAbbr: 'Pos.',
        team: 'Team',
        ptsTitle: 'Points accumulated',
        ptsAbbr: 'Pts',
        gamesTitle: 'Games played',
        gamesAbbr: 'GP',
        winsTitle: 'Wins',
        winsAbbr: 'W',
        drawsTitle: 'Draws',
        drawsAbbr: 'D',
        lossesTitle: 'Losses',
        lossesAbbr: 'L',
        noShowsTitle: 'Forfeits',
        noShowsAbbr: 'FF',
        goalDiffSymbol: '±',
        eloTrend: 'ELO Trend',
        eloTrendTitle: 'Shows the ELO rating evolution of the team in the last 5 games.\nMinimum ELO - Maximum ELO',
        form: 'Form',
        formTitle: 'Shows the last 5 results of the team (W=Win, D=Draw, L=Loss)\nLeft is oldest, right is most recent.',
        noDataAvailable: 'No data available',
        selectModality: 'Select a sport',
        selectModalityData: 'Select a sport to view the data',
        selectModalityBracket: 'Select a sport to view the bracket',
        selectModalityFirst: 'Select a sport first',
        removeFavorite: 'Remove from favorites',
        markFavorite: 'Mark as favorite',
        favoriteRemoved: 'Favorite team removed',
        favoriteSet: 'Favorite team:',
        eloCurrentTitle: 'Current ELO and overall ranking position',
        unknownDate: 'Unknown date',
        lastGame: 'last game',

        // === Weekdays ===
        weekdayShortSun: 'Sun',
        weekdayShortMon: 'Mon',
        weekdayShortTue: 'Tue',
        weekdayShortWed: 'Wed',
        weekdayShortThu: 'Thu',
        weekdayShortFri: 'Fri',
        weekdayShortSat: 'Sat',
        form: 'Form',
        placeLabel: 'place',

        // === Form (W/D/L) ===
        formWin: 'Win',
        formDraw: 'Draw',
        formLoss: 'Loss',
        formUnknown: 'Unknown',
        formWinLetter: 'W',
        formDrawLetter: 'D',
        formLossLetter: 'L',

        // === ELO Sparkline ===
        eloEvolution: 'ELO Evolution',
        lastGames: 'games',
        until: 'until',
        eloTrendAriaLabel: 'ELO Trend',

        // === ELO Chart ===
        eloChartTitle: 'Team ELO Evolution',
        eloQuickViews: 'Quick views',
        eloTeamsInChart: 'Teams in chart',
        eloChartTooltip: 'ELO represents the relative strength of teams throughout the season. It goes up with wins and down with losses.',
        expandCollapse: 'Expand/Collapse',
        previousSeason: '← Previous Season',
        nextSeason: 'Next Season →',
        teamsLabel: 'teams',

        // === Team Selector ===
        selectAll: 'Select All',
        deselectAll: 'Deselect All',
        invertSelection: 'Invert Selection',
        selectAllAria: 'Select all teams',
        deselectAllAria: 'Deselect all teams',
        invertSelectionAria: 'Invert team selection',
        allGroups: 'All',
        divisionGeneral: 'General Division',
        divisionNth: ' Division',
        teamSingular: 'team',
        teamPlural: 'teams',
        groupLabel: 'Group',

        // === Quick Filters ===
        filterTop3: 'Top 3',
        filterTop3Aria: 'Filter top 3 teams',
        filterByLabel: 'Filter by',
        filterByAllDiv2: 'Filter teams by all 2nd Division',
        playoffsLabel: 'Playoffs',
        playoffsCurrentRanking: 'Playoffs (Current Standings)',
        filterPlayoffsAria: 'Filter playoff teams',
        sensationTeams: 'Sensation Teams',
        sensationTeamsAria: 'Filter sensation teams with highest ELO gain',
        resetFilter: 'Reset Filter',
        resetFilterAria: 'Reset team filters',

        // === Calendar ===
        gameCalendar: 'Match Schedule',
        calendarSortAria: 'Calendar sorting',
        calendarSortDateTime: 'By Date/Time',
        calendarSortMatchday: 'By Matchday',
        calendarSortTeam: 'By Team',
        matchday: 'Matchday',
        calendarDateLabel: 'Date',
        calendarTeamPagePrefix: 'Team',
        selectMatchday: 'Select a matchday to see the games',
        noGamesFound: 'No games found for this matchday',
        noGamesFoundDateMode: 'No games found for this date',
        noGamesFoundTeamMode: 'No games found for this team',
        noGamesAvailable: 'No games available',
        noMatchdaysAvailable: 'No matchdays available',
        calendarNoDatePage: 'No scheduled date',
        dateToSchedule: 'DATE TBD',
        previousMatchday: 'Previous matchday',
        nextMatchday: 'Next matchday',
        navigatePrevious: 'Navigate to previous matchday',
        navigateNext: 'Navigate to next matchday',

        // === Brackets ===
        eliminationBracket: 'Elimination Bracket',
        playoffScenariosTitle: 'Playoff and Finals Scenarios',
        playoffLiguilha: 'Playoff/Play-in',
        secondaryBracketTitle: 'Maintenance/Play-in',
        maintenanceLiguillaScenariosTitle: 'Promotion/Maintenance Scenarios',
        maintenanceFirstPhase: '1st Phase',
        maintenanceFinalPhase: 'Final Phase',
        liguilhaRound1: 'Play-in 1',
        liguilhaRound2: 'Play-in 2',
        bracketNotAvailable: 'Bracket not available for this sport',
        thirdPlace: '3rd Place',
        bracketLabel1stDivision: '1st Division',
        bracketLabel2ndDivision: '2nd Division',
        bracketLabelLeague: 'of the League',
        bracketLabelGroup: 'Group',
        bracketQualificationSuffix: 'th',
        bracketWinner: 'Winner',
        bracketLoser: 'Loser',
        fourthPlace: '4th Place',
        predictedMatch: '📅 Predicted Matchup',
        unknownResult: '⚠️ Unknown Result',
        calendarPendingResultWarning: 'Result pending / Match postponed',
        quarterFinals: 'Quarterfinals',
        semiFinals: 'Semifinals',
        finals: 'Final',
        ofTheLeague: 'in League',
        div1st: '1st Div',
        div2nd: '2nd Div',
        groupAbbr: 'Gr.',

        // === Progression Legend ===
        playoffs: 'Playoffs',
        maintenancePlayoff: 'Maintenance Playoff',
        maintenanceLeague: 'Maintenance Play-in',
        relegation: 'Relegation',
        playoffsPromotion: 'Playoffs + Promotion',
        promotionPlayoff: 'Promotion Playoff',
        promotionLeague: 'Promotion Play-in',
        promotion: 'Promotion',
        safeZone: 'Safe zone',
        qualificationPlayoffs: 'Qualification for playoffs',
        replaces: 'replaces',
        ofGroup: 'of the group',
        teamBNoQualify: 'team B does not qualify',
        tiebreakIndicatorAria: 'Tiebreak indicator',
        tiebreakApplied: 'Tiebreak applied',
        tiebreakMiniLeague: 'Mini-league',
        tiebreakHeadToHead: 'Head-to-head',
        tiebreakTiePoints: 'Points tied',
        tiebreakTiedTeams: 'Tied teams',
        tiebreakCriteriaOrder: 'Criteria order',
        tiebreakDecidingCriterion: 'Deciding criterion',
        tiebreakAppliedByPosition: 'Applied criteria by position',
        tiebreakFallback: 'Global fallback',
        tiebreakFallbackYes: 'Yes',
        tiebreakFallbackNo: 'No',
        tiebreakTeamValues: 'Team values',
        tbFaltasComparencia: 'Absences',
        tbPointsH2H: 'Points (h2h)',
        tbNoShowsH2H: 'No-shows (h2h)',
        tbSetDiffH2H: 'Set difference (h2h)',
        tbScoreDiffH2H: 'Score difference (h2h)',
        tbScoreScoredH2H: 'Score scored (h2h)',
        tbBasketDiffH2H: 'Basket difference (h2h)',
        tbBasketsScoredH2H: 'Baskets scored (h2h)',
        tbSetsScoredH2H: 'Sets won (h2h)',
        tbGoalDiffH2H: 'Goal difference (h2h)',
        tbGoalsScoredH2H: 'Goals scored (h2h)',
        tbSetDiffOverall: 'Set difference (overall)',
        tbScoreDiffOverall: 'Score difference (overall)',
        tbScoreScoredOverall: 'Score scored (overall)',
        tbBasketDiffOverall: 'Basket difference (overall)',
        tbBasketsScoredOverall: 'Baskets scored (overall)',
        tbSetsScoredOverall: 'Sets won (overall)',
        tbGoalDiffOverall: 'Goal difference (overall)',
        tbGoalsScoredOverall: 'Goals scored (overall)',

        // === Predictions ===
        seasonPredictions: 'Season Predictions',
        teamDetailsTitle: 'Team Details',
        generalPredictions: 'GENERAL PREDICTIONS',
        teamSeasonOverview: 'Season Predictions',
        matchdayPredictions: 'Matchday-by-matchday Predictions',
        teamMatchHistory: 'Match History',
        predJornada: 'Matchday',
        predDate: 'Date',
        predOpponent: 'Opponent',
        predWinProb: 'P(W)',
        predWinProbTitle: 'Probability of win',
        predDrawProb: 'P(D)',
        predDrawProbTitle: 'Probability of draw',
        predLossProb: 'P(L)',
        predLossProbTitle: 'Probability of loss',
        expectedGoals: 'Expected Goals',
        expectedGoalsAbbr: 'Exp. Goals',
        expectedGoalsTitle: 'Expected goals',
        basketGoalsExpected: 'Exp. Points',
        basketGoalsTitle: 'Expected points',
        setsExpected: 'Exp. Sets',
        setsTitle: 'Expected sets',
        noStatsAvailable: 'No statistics available',
        noPredictionsData: 'No predictions data for this sport/season',
        noDataAvailableShort: 'No data available',
        errorLoading: 'Error loading',
        loading: 'Loading',
        showMore: 'Show more',
        loadingData: 'Loading data...',
        loadingRankings: 'Loading rankings...',
        noGamesForTeam: 'No predicted games for this team',
        noHistoryForTeam: 'No games available for this team',
        dataNotAvailable: 'Data not available',
        simulations: 'Simulations',
        eloDeltaLabel: 'ELO Delta',
        simulatedResults: 'Simulated Results',
        clickToFixTooltip: 'Click to pin/unpin distribution tooltip',
        previousTeam: 'Previous team',
        nextTeam: 'Next team',
        teamCarouselAria: 'Select a team for details',
        teamCarouselHint: 'Swipe or tap a team',
        seasonStart: 'Season Start',
        eloFinalPreviousSeason: 'Previous Season Final ELO',
        eloSeasonStart: 'Season Start ELO',
        interGroupAdjustments: 'Inter-Group Adjustments',
        eloRatingLabel: 'ELO Rating',

        // Dynamic headers per sport
        basketScored: 'Baskets made',
        basketConceded: 'Baskets conceded',
        basketDiff: 'Baskets difference (BM - BC)',
        setsWon: 'Sets won',
        setsLost: 'Sets lost',
        setsDiff: 'Sets difference (SW - SL)',
        goalsScored: 'Goals scored',
        goalsConceded: 'Goals conceded',
        goalsDiff: 'Goals difference (GS - GC)',

        // Prediction stats
        predPlayoffs: 'Playoffs',
        predSemiFinals: 'Semifinals',
        predFinal: 'Final',
        predChampionsMale: 'Champions',
        predChampionsFemale: 'Champions',
        predChampionsMaleDesc: 'Probability of being champions',
        predChampionsFemaleDesc: 'Probability of being champions',
        predQualification: 'Qualification probability',
        predReachSemis: 'Probability of reaching semifinals',
        predReachFinals: 'Probability of reaching the final',
        expectedPoints: 'Expected Points',
        expectedPosition: 'Expected Group Position',
        expectedValue: 'Expected value',
        positions: 'positions',
        points: 'points',
        avgFinalElo: 'Average Final ELO',
        predPromotion: 'Promotion',
        predPromotionDesc: 'Probability of promotion',
        predRelegation: 'Relegation',
        predRelegationDesc: 'Probability of relegation',
        predLiguillaLm1Play: 'Play LM1',
        predLiguillaLm1PlayDesc: 'Probability of playing Liguilla Round 1',
        predLiguillaLm1WinCond: 'Win LM1 (cond.)',
        predLiguillaLm1WinCondDesc: 'Probability of winning LM1, conditional on playing LM1',
        predLiguillaLm2PlayCond: 'Play LM2 (cond.)',
        predLiguillaLm2PlayCondDesc: 'Probability of playing LM2, conditional on playing LM1',
        predLiguillaLm2WinCond: 'Win LM2 (cond.)',
        predLiguillaLm2WinCondDesc: 'Probability of winning LM2, conditional on playing LM2',
        predLiguillaLm3PlayCond: 'Play LM3 (cond.)',
        predLiguillaLm3PlayCondDesc: 'Probability of playing LM3, conditional on playing LM2',
        predLiguillaLm3WinCond: 'Win LM3 (cond.)',
        predLiguillaLm3WinCondDesc: 'Probability of winning LM3, conditional on playing LM3',
        predLiguillaPromotion: 'Promotion via Liguilla',
        predLiguillaPromotionDesc: 'Overall promotion probability via LM1-LM3',
        liguillaScenariosGroupedTitle: 'Grouped Liguilla Scenarios',
        scenarioLabel: 'Scenario',
        scenarioProbability: 'Scenario probability',
        scenarioPassProbability: 'Probability to qualify in scenario',
        scenarioStayProbability: 'Probability of staying in the 1st Division',
        scenarioPromotionProbability: 'Probability of promotion',
        unknown: 'Unknown',

        // === Historical Tooltip ===
        historicalRankings: 'Rankings History',
        season: 'Season',
        group: 'Group',
        general: 'General',
        inProgress: 'In progress',
        didNotParticipate: 'Did not participate',
        as: 'As',

        // === Goals/Baskets/Sets (sport-specific) ===
        goalsScored: 'Goals scored',
        goalsConceded: 'Goals conceded',
        goalsDiff: 'Goal difference (GF - GA)',
        goalsExpected: 'Expected goals',
        goalsScoredAbbr: 'GF',
        goalsConcededAbbr: 'GA',
        goalsExpectedAbbr: 'Exp. Goals',
        basketsScored: 'Baskets scored',
        basketsConceded: 'Baskets conceded',
        basketsDiff: 'Basket difference (BS - BC)',
        basketsExpected: 'Expected baskets',
        basketsScoredAbbr: 'BS',
        basketsConcededAbbr: 'BC',
        basketsExpectedAbbr: 'Exp. Points',
        setsWon: 'Sets won',
        setsLost: 'Sets lost',
        setsDiff: 'Set difference (SW - SL)',
        setsExpected: 'Expected sets',
        setsWonAbbr: 'SW',
        setsLostAbbr: 'SL',
        setsExpectedAbbr: 'Expected Sets',

        // === Champions ===
        championsMale: 'Champions',
        championsViceMale: 'Runners-up',
        championsFemale: 'Champions',
        championsViceFemale: 'Runners-up',

        // === DivisionSelector ===
        div1Label: '1st Division',
        div2Label: '2nd Division',

        // === Sports/Modalities ===
        ANDEBOL_MISTO: 'Mixed Handball',
        BASQUETEBOL_FEMININO: 'Women\'s Basketball',
        BASQUETEBOL_MASCULINO: 'Men\'s Basketball',
        FUTEBOL_DE_7_MASCULINO: 'Men\'s 7-a-side Football',
        FUTSAL_FEMININO: 'Women\'s Futsal',
        FUTSAL_MASCULINO: 'Men\'s Futsal',
        VOLEIBOL_FEMININO: 'Women\'s Volleyball',
        VOLEIBOL_MASCULINO: 'Men\'s Volleyball',

        // === Division/Group Terms ===
        division: 'Division',
        group: 'Group',
        divisionLabel: ' Division',
        mainDivision: '1st Division',
        secondDivision: '2nd Division',
        groupA: 'Group A',
        groupB: 'Group B',
        groupC: 'Group C',
        groupD: 'Group D',

        // === Additional Terms ===
        selectAllTeams: 'Select All',
        deselectAllTeams: 'Deselect All',
        invertSelection: 'Invert Selection',
        teams: 'teams',
        team: 'team',
        thirdPlace: '3rd Place',
        fourthPlace: '4th Place',
        groupPrefix: 'Group ',
        divisionPrefix: ' Division',
        noMatchesAvailable: 'No matches available',
        roundOf: 'Round of ',
        vs: 'vs',
        home: 'Home',
        away: 'Away',
        draw: 'Draw',
        matchday: 'Matchday',
        date: 'Date',
        time: 'Time',
        location: 'Venue',
        locationToSchedule: 'VENUE TBD',
        provisionalDatePlaceholder: 'Provisional date - awaiting confirmation',
        provisionalLocationPlaceholder: 'Provisional venue - awaiting confirmation',
        opponent: 'Opponent',
        result: 'Result',
        score: 'Score',

        // === Round Labels (for short label use) ===
        roundQuarters: 'Quarterfinals',
        roundSemiFinals: 'Semifinals',
        roundFinal: 'Final',
        eloFinal: 'Final ELO',
        previousSeason: 'Previous Season',
        nextSeason: 'Next Season',

        // === Navbar ===
        navRankings: 'Rankings',
        navElo: 'ELO',
        navCalendar: 'Calendar',
        navBracket: 'Bracket',
        navPredictions: 'Details',

        // === Footer ===
        footerMadeBy: 'Project created by Fábio Matias',
        footerDisclaimer: 'This project is not officially associated with AAUAv and may contain inaccuracies',
        footerRepositoryAndDocs: 'Repository and documentation',
        footerResourcesLabel: 'Repository and documentation:',
        footerRepository: 'Repository',
        footerDocumentation: 'Documentation',
    }
};

translations.es = {
    // === Page / Meta ===
    pageTitle: 'Panel Taza UA',
    pageDescription: 'Panel interactivo de la Taza UA - Rankings, estadísticas ELO, calendario de partidos y cuadros de eliminación',

    // === Header ===
    dashboardTitle: 'Panel Taza UA',

    // === Selectors ===
    seasonLabel: 'Temporada:',
    modalityLabel: 'Modalidad:',

    // === Rankings ===
    generalRanking: 'Clasificación general',
    compactMode: 'Modo compacto',
    posTitle: 'Posición en la clasificación general',
    posAbbr: 'Pos.',
    team: 'Equipo',
    ptsTitle: 'Puntos acumulados',
    ptsAbbr: 'Pts',
    gamesTitle: 'Partidos jugados',
    gamesAbbr: 'PJ',
    winsTitle: 'Victorias',
    winsAbbr: 'V',
    drawsTitle: 'Empates',
    drawsAbbr: 'E',
    lossesTitle: 'Derrotas',
    lossesAbbr: 'D',
    noShowsTitle: 'Incomparecencias',
    noShowsAbbr: 'FF',
    goalDiffSymbol: '±',
    eloTrend: 'Tendencia ELO',
    eloTrendTitle: 'Muestra la evolución del rating ELO del equipo en los últimos 5 partidos.\nELO mínimo - ELO máximo',
    form: 'Forma',
    formTitle: 'Muestra los últimos 5 resultados del equipo (V=Victoria, E=Empate, D=Derrota)\nIzquierda es el más antiguo, derecha el más reciente.',
    noDataAvailable: 'No hay datos disponibles',
    selectModality: 'Selecciona una modalidad',
    selectModalityData: 'Selecciona una modalidad para ver los datos',
    selectModalityBracket: 'Selecciona una modalidad para ver el cuadro',
    selectModalityFirst: 'Selecciona una modalidad primero',
    removeFavorite: 'Quitar de favoritos',
    markFavorite: 'Marcar como favorito',
    favoriteRemoved: 'Equipo favorito eliminado',
    favoriteSet: 'Equipo favorito:',
    eloCurrentTitle: 'ELO actual y posición en el ranking general',
unknownDate: 'Fecha desconocida',
        lastGame: 'último partido',

        // === Días de la semana ===
        weekdayShortSun: 'Dom',
        weekdayShortMon: 'Lun',
        weekdayShortTue: 'Mar',
        weekdayShortWed: 'Mié',
        weekdayShortThu: 'Jue',
        weekdayShortFri: 'Vie',
        weekdayShortSat: 'Sáb',

        placeLabel: 'lugar',

    // === Form (W/D/L) ===
    formWin: 'Victoria',
    formDraw: 'Empate',
    formLoss: 'Derrota',
    formUnknown: 'Desconocido',
    formWinLetter: 'V',
    formDrawLetter: 'E',
    formLossLetter: 'D',

    // === ELO Sparkline ===
    eloEvolution: 'Evolución de ELO',
    lastGames: 'partidos',
    until: 'hasta',
    eloTrendAriaLabel: 'Tendencia de ELO',

    // === ELO Chart ===
    eloChartTitle: 'Evolución de ELO de los equipos',
    eloQuickViews: 'Vistas rápidas',
    eloTeamsInChart: 'Equipos en el gráfico',
    eloChartTooltip: 'ELO representa la fuerza relativa de los equipos durante la temporada. Sube con victorias, baja con derrotas.',
    expandCollapse: 'Expandir/Colapsar',
    previousSeason: '← Temporada anterior',
    nextSeason: 'Temporada siguiente →',
    teamsLabel: 'equipos',

    // === Team Selector ===
    selectAll: 'Seleccionar todas',
    deselectAll: 'Deseleccionar todas',
    invertSelection: 'Invertir selección',
    selectAllAria: 'Seleccionar todos los equipos',
    deselectAllAria: 'Deseleccionar todos los equipos',
    invertSelectionAria: 'Invertir selección de equipos',
    allGroups: 'Todos',
    divisionGeneral: 'División general',
    divisionNth: 'a División',
    teamSingular: 'equipo',
    teamPlural: 'equipos',
    groupLabel: 'Grupo',

    // === Quick Filters ===
    filterTop3: 'Top 3',
    filterTop3Aria: 'Filtrar top 3 equipos',
    filterByLabel: 'Filtrar por',
    filterByAllDiv2: 'Filtrar por toda la 2a División',
    playoffsLabel: 'Playoffs',
    playoffsCurrentRanking: 'Playoffs (Clasificación actual)',
    filterPlayoffsAria: 'Filtrar equipos de playoffs',
    sensationTeams: 'Equipos sorpresa',
    sensationTeamsAria: 'Filtrar equipos sorpresa con mayor aumento de ELO',
    resetFilter: 'Restablecer filtro',
    resetFilterAria: 'Restablecer filtros de equipos',

    // === Calendar ===
    gameCalendar: 'Calendario de partidos',
    calendarSortAria: 'Ordenación del calendario',
    calendarSortDateTime: 'Por Fecha/Hora',
    calendarSortMatchday: 'Por Jornada',
    matchday: 'Jornada',
    calendarDateLabel: 'Fecha',
    selectMatchday: 'Selecciona una jornada para ver los partidos',
    noGamesFound: 'No se encontraron partidos para esta jornada',
    noGamesFoundDateMode: 'No se encontraron partidos para esta fecha',
    noGamesAvailable: 'No hay partidos disponibles',
    noMatchdaysAvailable: 'No hay jornadas disponibles',
    calendarNoDatePage: 'Sin fecha definida',
    dateToSchedule: 'FECHA POR DEFINIR',
    previousMatchday: 'Jornada anterior',
    nextMatchday: 'Jornada siguiente',
    navigatePrevious: 'Navegar a la jornada anterior',
    navigateNext: 'Navegar a la jornada siguiente',

    // === Brackets ===
    eliminationBracket: 'Cuadro de eliminación',
    playoffScenariosTitle: 'Escenarios de Playoff y Finales',
    playoffLiguilha: 'Playoff/Liguilla',
    secondaryBracketTitle: 'Mantenimiento/Liguilla',
    maintenanceLiguillaScenariosTitle: 'Escenarios de Promoción/Mantenimiento',
    maintenanceFirstPhase: '1a Fase',
    maintenanceFinalPhase: 'Fase final',
    liguilhaRound1: 'Liguilla 1',
    liguilhaRound2: 'Liguilla 2',
    bracketNotAvailable: 'Cuadro no disponible para esta modalidad',
    thirdPlace: '3er Lugar',
    bracketLabel1stDivision: '1a División',
    bracketLabel2ndDivision: '2a División',
    bracketLabelLeague: 'de la Liga',
    bracketLabelGroup: 'Grupo',
    bracketQualificationSuffix: 'º',
    bracketWinner: 'Ganador',
    bracketLoser: 'Perdedor',
    fourthPlace: '4o Lugar',
    predictedMatch: '📅 Enfrentamiento previsto',
    unknownResult: '⚠️ Resultado desconocido',
    calendarPendingResultWarning: 'Resultado por publicar / Partido aplazado',
    quarterFinals: 'Cuartos de final',
    semiFinals: 'Semifinales',
    finals: 'Final',
    ofTheLeague: 'de la Liga',
    div1st: '1a Div',
    div2nd: '2a Div',
    groupAbbr: 'Gr.',

    // === Progression Legend ===
    playoffs: 'Playoffs',
    maintenancePlayoff: 'Playoff de mantenimiento',
    maintenanceLeague: 'Liguilla de mantenimiento',
    relegation: 'Descenso',
    playoffsPromotion: 'Playoffs + Promoción',
    promotionPlayoff: 'Playoff de promoción',
    promotionLeague: 'Liguilla de promoción',
    promotion: 'Ascenso',
    safeZone: 'Zona segura',
    tiebreakIndicatorAria: 'Indicador de desempate',
    tiebreakApplied: 'Desempate aplicado',
    tiebreakMiniLeague: 'Miniliga',
    tiebreakHeadToHead: 'Cara a cara',
    tiebreakTiePoints: 'Puntos empatados',
    tiebreakTiedTeams: 'Equipos empatados',
    tiebreakCriteriaOrder: 'Orden de criterios',
    tiebreakDecidingCriterion: 'Criterio decisivo',
    tiebreakAppliedByPosition: 'Criterios aplicados por posición',
    tiebreakFallback: 'Fallback global',
    tiebreakFallbackYes: 'Sí',
    tiebreakFallbackNo: 'No',
    tiebreakTeamValues: 'Valores del equipo',
    tbFaltasComparencia: 'Incomparecencias',
    tbPointsH2H: 'Puntos (h2h)',
    tbNoShowsH2H: 'Incomparecencias (h2h)',
    tbSetDiffH2H: 'Diferencia de sets (h2h)',
    tbScoreDiffH2H: 'Diferencia de score (h2h)',
    tbScoreScoredH2H: 'Score marcado (h2h)',
    tbBasketDiffH2H: 'Diferencia de cestas (h2h)',
    tbBasketsScoredH2H: 'Cestas anotadas (h2h)',
    tbSetsScoredH2H: 'Sets ganados (h2h)',
    tbGoalDiffH2H: 'Diferencia de goles (h2h)',
    tbGoalsScoredH2H: 'Goles marcados (h2h)',
    tbSetDiffOverall: 'Diferencia de sets (general)',
    tbScoreDiffOverall: 'Diferencia de score (general)',
    tbScoreScoredOverall: 'Score marcado (general)',
    tbBasketDiffOverall: 'Diferencia de cestas (general)',
    tbBasketsScoredOverall: 'Cestas anotadas (general)',
    tbSetsScoredOverall: 'Sets ganados (general)',
    tbGoalDiffOverall: 'Diferencia de goles (general)',
    tbGoalsScoredOverall: 'Goles marcados (general)',

    // === Predictions ===
    seasonPredictions: 'Predicciones de la temporada',
    teamDetailsTitle: 'Detalles de los equipos',
    generalPredictions: 'PREDICCIONES GENERALES',
    teamSeasonOverview: 'Predicciones de la temporada',
    matchdayPredictions: 'Predicciones jornada a jornada',
    teamMatchHistory: 'Historial de partidos',
    predJornada: 'Jornada',
    predDate: 'Fecha',
    predOpponent: 'Rival',
    predWinProb: 'P(V)',
    predWinProbTitle: 'Probabilidad de victoria',
    predDrawProb: 'P(E)',
    predDrawProbTitle: 'Probabilidad de empate',
    predLossProb: 'P(D)',
    predLossProbTitle: 'Probabilidad de derrota',
    expectedGoals: 'Goles esp.',
    expectedGoalsAbbr: 'Goles esp.',
    expectedGoalsTitle: 'Goles esperados',
    basketGoalsExpected: 'Puntos esp.',
    basketGoalsTitle: 'Puntos esperados',
    setsExpected: 'Sets esp.',
    setsTitle: 'Sets esperados',
    noStatsAvailable: 'No hay estadísticas disponibles',
    noPredictionsData: 'No hay datos de predicciones para esta modalidad/temporada',
    noDataAvailableShort: 'No hay datos disponibles',
errorLoading: 'Error al cargar',
        loading: 'Cargando',
        showMore: 'Ver más',
        loadingData: 'Cargando datos...',
    loadingRankings: 'Cargando clasificación...',
    noGamesForTeam: 'No hay partidos previstos para este equipo',
    noHistoryForTeam: 'No hay partidos disponibles para este equipo',
    dataNotAvailable: 'Datos no disponibles',
    simulations: 'simulaciones',
    simulatedResults: 'Resultados simulados',
    eloDeltaLabel: 'Delta ELO',
    clickToFixTooltip: 'Haz clic para fijar/desfijar el tooltip de distribución',
    previousTeam: 'Equipo anterior',
    nextTeam: 'Equipo siguiente',
    teamCarouselAria: 'Seleccionar equipo para ver detalles',
    teamCarouselHint: 'Desliza o toca un equipo',

    // Dynamic headers per sport
    basketScored: 'Canastas anotadas',
    basketConceded: 'Canastas recibidas',
    basketDiff: 'Diferencia de canastas (CA - CR)',
    setsWon: 'Sets ganados',
    setsLost: 'Sets perdidos',
    setsDiff: 'Diferencia de sets (SG - SP)',
    goalsScored: 'Goles marcados',
    goalsConceded: 'Goles recibidos',
    goalsDiff: 'Diferencia de goles (GM - GR)',

    // Prediction stats
    predPlayoffs: 'Playoffs',
    predSemiFinals: 'Semifinales',
    predFinal: 'Final',
    predChampionsMale: 'Campeones',
    predChampionsFemale: 'Campeonas',
    predChampionsMaleDesc: 'Probabilidad de ser campeones',
    predChampionsFemaleDesc: 'Probabilidad de ser campeonas',
    predQualification: 'Probabilidad de clasificación',
    predReachSemis: 'Probabilidad de llegar a semifinales',
    predReachFinals: 'Probabilidad de llegar a la final',
    expectedPoints: 'Puntos esperados',
    expectedPosition: 'Posición esperada en el grupo',
    expectedValue: 'Valor esperado',
    positions: 'posiciones',
    points: 'puntos',
    avgFinalElo: 'ELO final medio',
    predPromotion: 'Promoción',
    predPromotionDesc: 'Probabilidad de ascenso',
    predRelegation: 'Descenso',
    predRelegationDesc: 'Probabilidad de descenso',
    predLiguillaLm1Play: 'Disputa LM1',
    predLiguillaLm1PlayDesc: 'Probabilidad de disputar la Liguilla 1',
    predLiguillaLm1WinCond: 'Gana LM1 (cond.)',
    predLiguillaLm1WinCondDesc: 'Probabilidad de ganar LM1, dado que disputa LM1',
    predLiguillaLm2PlayCond: 'Disputa LM2 (cond.)',
    predLiguillaLm2PlayCondDesc: 'Probabilidad de disputar LM2, dado que disputa LM1',
    predLiguillaLm2WinCond: 'Gana LM2 (cond.)',
    predLiguillaLm2WinCondDesc: 'Probabilidad de ganar LM2, dado que disputa LM2',
    predLiguillaLm3PlayCond: 'Disputa LM3 (cond.)',
    predLiguillaLm3PlayCondDesc: 'Probabilidad de disputar LM3, dado que disputa LM2',
    predLiguillaLm3WinCond: 'Gana LM3 (cond.)',
    predLiguillaLm3WinCondDesc: 'Probabilidad de ganar LM3, dado que disputa LM3',
    predLiguillaPromotion: 'Promoción vía Liguilla',
    predLiguillaPromotionDesc: 'Probabilidad total de ascenso vía LM1-LM3',
    liguillaScenariosGroupedTitle: 'Escenarios Agrupados de Liguilla',
    scenarioLabel: 'Escenario',
    scenarioProbability: 'Probabilidad del escenario',
    scenarioPassProbability: 'Probabilidad de pasar en el escenario',
    scenarioStayProbability: 'Probabilidad de permanecer en 1ª División',
    scenarioPromotionProbability: 'Probabilidad de ascender',
    unknown: 'Desconocido',
    qualificationPlayoffs: 'Clasificación para playoffs',
    replaces: 'sustituye',
    ofGroup: 'del grupo',
    teamBNoQualify: 'el equipo B no clasifica',
    seasonStart: 'Inicio de la temporada',
    eloFinalPreviousSeason: 'ELO final de la temporada anterior',
    eloSeasonStart: 'ELO de inicio de temporada',
    interGroupAdjustments: 'Ajustes intergrupos',
    eloRatingLabel: 'Rating ELO',

    // === Historical Tooltip ===
    historicalRankings: 'Histórico de clasificaciones',
    season: 'Temporada',
    group: 'Grupo',
    general: 'General',
    inProgress: 'en curso',
    didNotParticipate: 'No participó',
    as: 'Como',

    // === Goals/Baskets/Sets (sport-specific) ===
    goalsExpected: 'Goles esperados',
    goalsScoredAbbr: 'GF',
    goalsConcededAbbr: 'GC',
    goalsExpectedAbbr: 'Goles esp.',
    basketsScored: 'Canastas anotadas',
    basketsConceded: 'Canastas recibidas',
    basketsDiff: 'Diferencia de canastas (CA - CR)',
    basketsExpected: 'Canastas esperadas',
    basketsScoredAbbr: 'CA',
    basketsConcededAbbr: 'CR',
    basketsExpectedAbbr: 'Puntos esp.',
    setsExpected: 'Sets esperados',
    setsWonAbbr: 'SG',
    setsLostAbbr: 'SP',
    setsExpectedAbbr: 'Sets esp.',

    // === Champions ===
championsMale: 'Campeones',
    championsViceMale: 'Subcampeones',
    championsFemale: 'Campeonas',
    championsViceFemale: 'Subcampeonas',

    // === DivisionSelector ===
    div1Label: '1a División',
    div2Label: '2a División',

    // === Sports/Modalities ===
    ANDEBOL_MISTO: 'Balonmano mixto',
    BASQUETEBOL_FEMININO: 'Baloncesto femenino',
    BASQUETEBOL_MASCULINO: 'Baloncesto masculino',
    FUTEBOL_DE_7_MASCULINO: 'Fútbol 7 masculino',
    FUTSAL_FEMININO: 'Futsal femenino',
    FUTSAL_MASCULINO: 'Futsal masculino',
    VOLEIBOL_FEMININO: 'Voleibol femenino',
    VOLEIBOL_MASCULINO: 'Voleibol masculino',

    // === Division/Group Terms ===
    division: 'División',
    group: 'Grupo',
    divisionLabel: 'a División',
    mainDivision: '1a División',
    secondDivision: '2a División',
    groupA: 'Grupo A',
    groupB: 'Grupo B',
    groupC: 'Grupo C',
    groupD: 'Grupo D',

    // === Additional Terms ===
    selectAllTeams: 'Seleccionar todas',
    deselectAllTeams: 'Deseleccionar todas',
    invertSelection: 'Invertir selección',
    teams: 'equipos',
    team: 'equipo',
    fourthPlace: '4o Lugar',
    groupPrefix: 'Grupo ',
    divisionPrefix: 'a División',
    noMatchesAvailable: 'No hay partidos disponibles',
    roundOf: 'Ronda de ',
    vs: 'vs',
    home: 'Local',
    away: 'Visitante',
    draw: 'Empate',
    matchday: 'Jornada',
    date: 'Fecha',
    time: 'Hora',
    location: 'Lugar',
    locationToSchedule: 'LUGAR POR DEFINIR',
    provisionalDatePlaceholder: 'Fecha provisional - esperando confirmación',
    provisionalLocationPlaceholder: 'Lugar provisional - esperando confirmación',
    opponent: 'Rival',
    result: 'Resultado',
    score: 'Puntuación',

    // === Round Labels (for short label use) ===
    roundQuarters: 'Cuartos',
    roundSemiFinals: 'Semis',
    roundFinal: 'Final',
    eloFinal: 'ELO final',
    previousSeason: 'Temporada anterior',
    nextSeason: 'Temporada siguiente',

    // === Navbar ===
    navRankings: 'Rankings',
    navElo: 'ELO',
    navCalendar: 'Calendario',
    navBracket: 'Bracket',
    navPredictions: 'Detalles',

    // === Footer ===
    footerMadeBy: 'Proyecto creado por Fábio Matias',
    footerDisclaimer: 'Este proyecto no está oficialmente asociado con AAUAv y puede contener imprecisiones',
    footerRepositoryAndDocs: 'Repositorio y documentación',
    footerResourcesLabel: 'Repositorio y documentación:',
    footerRepository: 'Repositorio',
    footerDocumentation: 'Documentación'
};

// ==================== FUNÇÕES DO i18n ====================

let currentLanguage = localStorage.getItem('mmr_selectedLanguage') || localStorage.getItem('dashboardLanguage') || 'pt';

/** * Traduz um nome de equipa para o idioma atual
 * @param {string} teamNamePt - Nome da equipa em português
 * @returns {string} Nome traduzido
 */
function translateTeamName(teamNamePt) {
    if (!teamNamePt) return '';

    // Se o idioma é português, retorna o nome original
    if (currentLanguage === 'pt') {
        return teamNamePt;
    }

    // Procurar no mapeamento de tradução
    const translationMap = teamNamesTranslation[currentLanguage] || teamNamesTranslation.pt;
    if (translationMap && translationMap[teamNamePt]) {
        return translationMap[teamNamePt];
    }

    // Fallback: retornar o nome original se não houver tradução
    return teamNamePt;
}

/** * Obtém a tradução para uma chave.
 * Fallback para português se a chave não existir no idioma atual.
 * @param {string} key - Chave de tradução
 * @returns {string} Texto traduzido
 */
function t(key) {
    const lang = translations[currentLanguage];
    if (lang && lang[key] !== undefined) {
        return lang[key];
    }
    // Fallback para português
    if (translations.pt[key] !== undefined) {
        return translations.pt[key];
    }
    // Se nem em PT existe, retorna a chave
    console.warn(`[i18n] Missing translation key: "${key}"`);
    return key;
}

/**
 * Define o idioma atual e persiste no localStorage
 * @param {string} lang - Código do idioma ('pt', 'en' ou 'es')
 */
function setLanguage(lang) {
    if (!translations[lang]) {
        console.warn(`[i18n] Language "${lang}" not supported`);
        return;
    }
    currentLanguage = lang;
    localStorage.setItem('mmr_selectedLanguage', lang);

    // Atualizar o atributo lang do HTML
    document.documentElement.lang = lang;

    // Aplicar traduções estáticas
    applyStaticTranslations();

    // Atualizar título da página
    document.title = t('pageTitle');

    // Atualizar meta description
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) {
        metaDesc.setAttribute('content', t('pageDescription'));
    }

    // Re-renderizar todo o conteúdo dinâmico
    refreshAllContent();
}

/**
 * Obtém o idioma atual
 * @returns {string} Código do idioma
 */
function getCurrentLanguage() {
    return currentLanguage;
}

/**
 * Aplica traduções a todos os elementos com data-i18n e data-i18n-title
 */
function applyStaticTranslations() {
    // Traduzir textContent
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        el.textContent = t(key);
    });

    // Traduzir atributos title
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        el.setAttribute('title', t(key));
    });

    // Traduzir placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        el.setAttribute('placeholder', t(key));
    });

    // Traduzir aria-labels
    document.querySelectorAll('[data-i18n-aria]').forEach(el => {
        const key = el.getAttribute('data-i18n-aria');
        el.setAttribute('aria-label', t(key));
    });
}

/**
 * Re-renderiza todo o conteúdo dinâmico após mudança de idioma
 */
function refreshAllContent() {
    // Atualizar labels dos seletores de época/modalidade
    if (typeof updateSelectorLabels === 'function') {
        try {
            updateSelectorLabels();
        } catch (e) { }
    }

    // Verificar se a app já foi inicializada
    if (typeof updateRankingsTable === 'function') {
        try {
            if (typeof createDivisionSelector === 'function') {
                createDivisionSelector();
            }
            if (typeof updateGroupSelector === 'function') {
                updateGroupSelector();
            }
            updateRankingsTableHeaders();
            updateRankingsTable();
            if (typeof updateRankingsDivisionButtons === 'function') {
                updateRankingsDivisionButtons();
            }
            if (typeof updateRankingsGroupButtons === 'function') {
                updateRankingsGroupButtons();
            }
        } catch (e) { /* Silenciar se não há dados */ }
    }

    if (typeof updateCalendar === 'function') {
        try {
            if (typeof createCalendarDivisionSelector === 'function') {
                createCalendarDivisionSelector();
            }
            if (typeof createCalendarGroupSelector === 'function') {
                createCalendarGroupSelector();
            }
            if (typeof updateCalendarSortControls === 'function') {
                updateCalendarSortControls();
            }
            updateJornadaDisplay();
            updateCalendar();
        } catch (e) { }
    }

    if (typeof createBracket === 'function') {
        try {
            createBracket();
            createSecondaryBracket();
        } catch (e) { }
    }

    if (typeof updateEloChart === 'function') {
        try {
            updateEloChart();
            createTeamSelector();
            updateQuickFilters();
            updateTeamCountIndicator();
            updateSeasonNavigationButtons();
        } catch (e) { }
    }

    if (typeof updatePredictionsDisplay === 'function') {
        try {
            if (typeof updatePredictionsSelectors === 'function') {
                updatePredictionsSelectors();
            }
            updatePredictionsDisplay();
            updatePredictionsSimulationsCount();
            updatePredictionsTableHeaders();
        } catch (e) { }
    }
}

/**
 * Inicializa o seletor de idioma na UI
 */
function initLanguageSelector() {
    // Procurar primeiro no navbar
    let container = document.querySelector('#navbarLanguageSelector');
    // Fallback para header antigo
    if (!container) {
        const header = document.querySelector('.header');
        if (header) {
            const selectorDiv = document.createElement('div');
            selectorDiv.className = 'language-selector';
            selectorDiv.id = 'languageSelector';
            container = selectorDiv;
            header.appendChild(container);
        } else {
            return;
        }
    }

    // Limpar container se tiver conteúdo anterior
    container.innerHTML = '';

    // Botão PT
    const ptBtn = document.createElement('button');
    ptBtn.className = `lang-btn ${currentLanguage === 'pt' ? 'active' : ''}`;
    ptBtn.id = 'lang-pt';
    ptBtn.setAttribute('aria-label', 'Português');
    ptBtn.title = 'Português';
    ptBtn.innerHTML = '🇵🇹';
    ptBtn.addEventListener('click', () => {
        setLanguage('pt');
        updateLanguageButtons('pt');
    });

    // Botão EN
    const enBtn = document.createElement('button');
    enBtn.className = `lang-btn ${currentLanguage === 'en' ? 'active' : ''}`;
    enBtn.id = 'lang-en';
    enBtn.setAttribute('aria-label', 'English');
    enBtn.title = 'English';
    enBtn.innerHTML = '🇬🇧';
    enBtn.addEventListener('click', () => {
        setLanguage('en');
        updateLanguageButtons('en');
    });

    // Botão ES
    const esBtn = document.createElement('button');
    esBtn.className = `lang-btn ${currentLanguage === 'es' ? 'active' : ''}`;
    esBtn.id = 'lang-es';
    esBtn.setAttribute('aria-label', 'Español');
    esBtn.title = 'Español';
    esBtn.innerHTML = '🇪🇸';
    esBtn.addEventListener('click', () => {
        setLanguage('es');
        updateLanguageButtons('es');
    });

    container.appendChild(ptBtn);
    container.appendChild(enBtn);
    container.appendChild(esBtn);

    // Aplicar idioma guardado
    if (currentLanguage !== 'pt') {
        setLanguage(currentLanguage);
    }
}

/**
 * Atualiza os botões de idioma (estado ativo)
 */
function updateLanguageButtons(lang) {
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    const activeBtn = document.getElementById(`lang-${lang}`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
}

// Inicializar seletor quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', initLanguageSelector);

// Garantir que t() está acessível globalmente (importante para tooltips e contextos dinâmicos)
window.t = t;
window.translateTeamName = translateTeamName;
window.setLanguage = setLanguage;
window.getCurrentLanguage = getCurrentLanguage;
