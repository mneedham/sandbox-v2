package com.neo4j.sandbox.security;

import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.PathParam;
import javax.ws.rs.Produces;
import javax.ws.rs.core.Context;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;
import javax.ws.rs.core.Response.Status;
import org.neo4j.string.UTF8;
import org.neo4j.server.rest.security.SecurityRule;
import org.neo4j.server.rest.security.SecurityFilter;
import javax.servlet.http.HttpServletRequest;

public class SandboxAuthSecurityRule implements SecurityRule
{
    public static final String REALM = "Neo4j"; // as per RFC2617 :-)

    @Override
    public boolean isAuthorized( HttpServletRequest request )
    {
	System.out.println("RETURNING AUTHORIZED");
        return true; // always succeeds
    }

    @Override
    public String forUriPath()
    {
	System.out.println("ASKED FOR PATH");
        return "/sandbox-auth*";
    }

    @Override
    public String wwwAuthenticateHeader()
    {
	System.out.println("RETURNING HEADER");
        return SecurityFilter.basicAuthenticationResponse(REALM);
    }
}
