package com.neo4j.sandbox.security;

import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Collections;
import java.util.Optional;
import java.util.Properties;
import java.util.Map;

import org.neo4j.server.security.enterprise.auth.plugin.api.AuthToken;
import org.neo4j.server.security.enterprise.auth.plugin.api.AuthenticationException;
import org.neo4j.server.security.enterprise.auth.plugin.api.PredefinedRoles;
import org.neo4j.server.security.enterprise.auth.plugin.api.AuthProviderOperations;
import org.neo4j.server.security.enterprise.auth.plugin.spi.AuthInfo;
import org.neo4j.server.security.enterprise.auth.plugin.spi.AuthPlugin;

import java.security.cert.Certificate;
import java.security.cert.CertificateFactory;
import java.security.cert.X509Certificate;
import java.security.PublicKey;
import java.security.interfaces.RSAKey;
import com.auth0.jwt.JWT;
import com.auth0.jwt.JWTVerifier;
import com.auth0.jwt.algorithms.Algorithm;
import com.auth0.jwt.interfaces.DecodedJWT;
import com.auth0.jwt.exceptions.JWTVerificationException;

public class SandboxAuthPlugin extends AuthPlugin.Adapter
{
    private AuthProviderOperations api;
    private String certificatePath;
    private String jwtAudience;
    private String jwtIssuer;
    private String sandboxUser = null;

    @Override
    public AuthInfo authenticateAndAuthorize( AuthToken authToken ) throws AuthenticationException
    {
        String username = authToken.principal();
        char[] password = authToken.credentials();

        api.log().info( "Log in attempted for user '" + username + "'.");

        if ( username != null && password != null && sandboxUser != null )
        {
            if (username.equals("jwt")) {
              String token = String.valueOf(password);
              try {
                CertificateFactory fact = CertificateFactory.getInstance("X.509");
                FileInputStream is = new FileInputStream (certificatePath);
                X509Certificate cer = (X509Certificate) fact.generateCertificate(is);
                RSAKey key = (RSAKey) cer.getPublicKey();
                
                DecodedJWT jwt = JWT.require(Algorithm.RSA256(key))
                   .withIssuer(jwtIssuer)
                   .withSubject(sandboxUser)
                   .withAudience(jwtAudience)
                   .build().verify(token);
                api.log().info("JWT successfully verified for sandbox user: " + sandboxUser);
                return AuthInfo.of( "neo4j", Collections.singleton( PredefinedRoles.ADMIN ) );
              } catch (JWTVerificationException ex){
                api.log().info("JWT verification exception: " + ex.getMessage());
                return null;
              } catch (Exception ex) {
                api.log().error("Other exception verifying JWT: " + ex.getMessage());
                return null;
              }
            } 
        }
        return null;
    }

    @Override
    public void initialize( AuthProviderOperations authProviderOperations )
    {
        api = authProviderOperations;

        /* 
         * verification of a JWT is cheap. exceptions for expired authorization
         * cache aren't handled well by Neo4j Browser, so disable for now
         */
        api.setAuthenticationCachingEnabled(false);
        api.setAuthorizationCachingEnabled(false);
        api.log().info( "initialized!" );

        loadConfig();
    }

    private void loadConfig()
    {
        Path configFile = resolveConfigFilePath();
        Properties properties = loadProperties( configFile );

        certificatePath = properties.getProperty( "com.neo4j.sandbox.security.certificate" );
        api.log().info( "com.neo4j.sandbox.security.certificate=" + certificatePath );

        jwtAudience = properties.getProperty( "com.neo4j.sandbox.security.jwtaud" );
        api.log().info( "com.neo4j.sandbox.security.jwtaud=" + jwtAudience);

        jwtIssuer = properties.getProperty( "com.neo4j.sandbox.security.jwtiss" );
        api.log().info( "com.neo4j.sandbox.security.jwtiss=" + jwtIssuer);

        Map<String, String> env = System.getenv();
        if (env.containsKey("SANDBOX_USER")) {
            sandboxUser = env.get("SANDBOX_USER");
        }
    }

    private Path resolveConfigFilePath()
    {
        Path configFilePath;
        Optional<Path> maybeConfigFile = api.neo4jConfigFile();

        if ( maybeConfigFile.isPresent() )
        {
            configFilePath = maybeConfigFile.get();
        }
        else
        {
            configFilePath = api.neo4jHome().resolve( "conf/neo4j.conf" );
        }
        return configFilePath;
    }

    private Properties loadProperties( Path configFile )
    {
        Properties properties = new Properties();

        try
        {
            InputStream inputStream = new FileInputStream( configFile.toFile() );
            properties.load( inputStream );
        }
        catch ( IOException e )
        {
            api.log().error( "Failed to load config file '" + configFile.toString() + "'." );
        }
        return properties;
    }
}
