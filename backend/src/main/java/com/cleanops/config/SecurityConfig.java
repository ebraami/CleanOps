package com.cleanops.config;

import com.cleanops.security.FirebaseAuthenticationFilter;
import com.google.auth.oauth2.AccessToken;
import com.google.auth.oauth2.GoogleCredentials;
import com.google.firebase.FirebaseApp;
import com.google.firebase.FirebaseOptions;
import java.io.IOException;
import java.util.Date;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.annotation.Order;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

@Configuration
public class SecurityConfig {

    /**
     * Initializes Firebase Admin with Application Default Credentials.
     * Configure GOOGLE_APPLICATION_CREDENTIALS to point to a service-account JSON
     * file locally, or use the hosting platform's attached service account.
     * Includes development fallback when credentials are not present.
     */
    @Bean
    public FirebaseApp firebaseApp() throws IOException {
        if (!FirebaseApp.getApps().isEmpty()) {
            return FirebaseApp.getInstance();
        }

        GoogleCredentials credentials;
        try {
            credentials = GoogleCredentials.getApplicationDefault();
        } catch (Exception e) {
            // Development fallback when no GCP service-account file is present
            credentials = GoogleCredentials.create(
                new AccessToken("dev-token", new Date(System.currentTimeMillis() + 86400000))
            );
        }

        FirebaseOptions options = FirebaseOptions.builder()
                .setCredentials(credentials)
                .setProjectId("cleanops-dev")
                .build();
        return FirebaseApp.initializeApp(options);
    }

    @Bean
    public FirebaseAuthenticationFilter firebaseAuthenticationFilter() {
        return new FirebaseAuthenticationFilter();
    }

    /** Protect every /api/v1/** endpoint using a verified Firebase ID token. */
    @Bean
    @Order(1)
    public SecurityFilterChain apiSecurityFilterChain(
            HttpSecurity http,
            FirebaseAuthenticationFilter firebaseAuthenticationFilter) throws Exception {
        http
                .securityMatcher("/api/v1/**")
                .csrf(csrf -> csrf.disable())
                .cors(Customizer.withDefaults())
                .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(authorize -> authorize.anyRequest().authenticated())
                .addFilterBefore(firebaseAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);
        return http.build();
    }

    /** Leave non-API routes (for example health checks or static assets) outside this API token filter. */
    @Bean
    @Order(2)
    public SecurityFilterChain otherRoutesSecurityFilterChain(HttpSecurity http) throws Exception {
        http
                .csrf(csrf -> csrf.disable())
                .authorizeHttpRequests(authorize -> authorize.anyRequest().permitAll());
        return http.build();
    }
}
