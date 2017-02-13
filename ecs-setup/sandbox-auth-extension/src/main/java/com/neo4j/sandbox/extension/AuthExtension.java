package com.neo4j.sandbox.extension;

import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.PathParam;
import javax.ws.rs.Produces;
import javax.ws.rs.core.Context;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;
import javax.ws.rs.core.Response.Status;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.io.IOException;
import java.net.URISyntaxException;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.InputStream;

import org.neo4j.graphdb.GraphDatabaseService;
import org.neo4j.string.UTF8;
import org.apache.commons.io.IOUtils;

@Path( "" )
public class AuthExtension
{
    private final GraphDatabaseService database;

public String readFileFromClasspath(final String fileName) throws IOException, URISyntaxException {
    InputStream in = getClass().getClassLoader().getResourceAsStream(fileName);
    BufferedReader reader = new BufferedReader(new InputStreamReader(in));
    String message = org.apache.commons.io.IOUtils.toString(reader);
    return message;
}


    public AuthExtension( @Context GraphDatabaseService database )
    {
        this.database = database;
    }

    @GET
    @Produces( MediaType.TEXT_HTML)
    @Path( "/setauthtoken" )
    public Response setLocalStorage()
    {   
        try {
          String msg = readFileFromClasspath("sandbox-auth/index.html");
          return Response.status( Status.OK ).entity( UTF8.encode( msg ) ).build();
        } catch (Exception ex) {
          ex.printStackTrace();
          return Response.status( 500 ).entity( UTF8.encode( "Error opening file" ) ).build();
        }
    }
}
