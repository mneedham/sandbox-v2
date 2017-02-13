package com.neo4j.sandbox.extension.lifecycle;
import org.apache.commons.configuration.Configuration;
import org.neo4j.graphdb.GraphDatabaseService;
import org.neo4j.server.AbstractNeoServer;
import org.neo4j.server.NeoServer;
import org.neo4j.server.plugins.Injectable;
import org.neo4j.server.plugins.SPIPluginLifecycle;
import org.neo4j.server.web.WebServer;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;

public final class SandboxLifecycle implements SPIPluginLifecycle {

    private WebServer webServer;
    //private ApiVersionVerifierFilter apiVersionVerifierFilter;

    @Override
    public Collection<Injectable<?>> start(final NeoServer neoServer) {
        webServer = getWebServer(neoServer);
        addFilters();
        return Collections.emptyList();
    }

    @Override
    public void stop() {
        removeFilters();
    }

    @Override
    public Collection<Injectable<?>> start(final GraphDatabaseService graphDatabaseService,
                                         final Configuration config) {
        throw new IllegalAccessError();
    }

    private WebServer getWebServer(final NeoServer neoServer) {
      if (neoServer instanceof AbstractNeoServer) {
          return ((AbstractNeoServer) neoServer).getWebServer();
      }
      throw new IllegalArgumentException(String.format("Expected: [AbstractNeoServer], Received: [%s].", neoServer));
    }

    private void addFilters() {
        webServer.addStaticContent("sandbox-auth", "/browser/sandbox-auth");
        //apiVersionVerifierFilter = new ApiVersionVerifierFilter();
        //webServer.addFilter(apiVersionVerifierFilter, "/extension-path/*");
    }

    private void removeFilters() {
        webServer.addStaticContent("sandbox-auth", "/browser/sandbox-auth");
        //webServer.removeFilter(apiVersionVerifierFilter, "/extension-path/*");
    }
}
