getUserFromSlug = """
query userFromSlug($slug: String!) {
  user(slug: $slug) {
    id
    discriminator
    player {
      gamerTag
    }  
  }
}
"""

getAllTournamentsWA = """
query tournament($page: Int!, $ids: [ID!], $after: Timestamp!, $before: Timestamp!) {
  tournaments(query: {
  	page: $page
    perPage: 50
    
    #filters for US Washinton, Ultimate, and date
    filter: {
    	countryCode: "US"
    	addrState: "WA"
      videogameIds: $ids
      past: true
      afterDate: $after
      beforeDate: $before
      hasOnlineEvents: false
    }
  }) {
    #get total tournaments, and amount of pages
    pageInfo {
      total
      totalPages
    }
    nodes {
      #id, name, slug for constructing links, numAttendees for score bonus
      id
      name
      slug
      numAttendees
      state
      startAt
      #events
      events(
        limit: 0,
        filter: {
          #only ultimate, and type 1 is singles
          videogameId: $ids
          type: 1
        }
      ) {
        #event id, and name for checking if it contains "singles"
        id
        name
        state
      }
      #owner for verification its a valid WWA PR TO responsible
      owner {
        #gamertag for anonymity
        player {
          gamerTag
        }
        #discriminator and id
        discriminator
        id
      }
    }
  }
}"""

getAllTournamentsNO = """
query tournament($page: Int!, $ids: [ID!], $after: Timestamp!, $before: Timestamp!) {
  tournaments(query: {
  	page: $page
    perPage: 50
    
    #filters for US Washinton, Ultimate, and date
    filter: {
    	countryCode: "NO"
      videogameIds: $ids
      past: true
      afterDate: $after
      beforeDate: $before
      hasOnlineEvents: false
    }
  }) {
    #get total tournaments, and amount of pages
    pageInfo {
      total
      totalPages
    }
    nodes {
      #id, name, slug for constructing links, numAttendees for score bonus
      id
      name
      slug
      numAttendees
      state
      startAt
      #events
      events(
        limit: 0,
        filter: {
          #only ultimate, and type 1 is singles
          videogameId: $ids
          type: 1
        }
      ) {
        #event id, and name for checking if it contains "singles"
        id
        name
        state
      }
      #owner for verification its a valid WWA PR TO responsible
      owner {
        #gamertag for anonymity
        player {
          gamerTag
        }
        #discriminator and id
        discriminator
        id
      }
    }
  }
}"""

setsInTournament = """
query sets($id: ID!, $page: Int!, $entrantIds: [ID!]) {
  event(id: $id) {
    sets(
      page: $page
      perPage: 200
      filters: {
        entrantIds: $entrantIds
      }
    ){
      pageInfo {
        total
        totalPages
      }
      nodes {
        slots {
          standing {
            placement
            entrant { 
              id
            }
          }
        }
      }
    }
  }
}"""

getTournamentEntrants = """
query slugEvent($page: Int!, $slug: String!) {
  event(slug: $slug) {
    id
    name
    state
    tournament{
      name
      id
      state
      slug
      startAt
      owner {
        id
        discriminator
        player {
          gamerTag
        }
      }
    }
    entrants(query: {
      page: $page
      perPage: 100
    }) {
      pageInfo {
        totalPages
      }
      nodes {
        id
        standing {
          placement
        }
        participants {
          gamerTag
          user {
            id
            discriminator
          }
        }
      }
    }
  }
}
"""

getAllEventEntrants = """
query events($id: ID!, $page: Int!) {
  event(id: $id) {
    entrants(query: {
      page: $page
      perPage: 100
    }) {
      pageInfo {
        total
        totalPages
      }
      nodes {
        id
        standing {
          placement
        }
        participants {
          gamerTag
          user {
            id
            discriminator
          }
        }
      }
    }
  }
}"""