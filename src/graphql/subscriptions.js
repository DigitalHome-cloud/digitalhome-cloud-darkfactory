/* eslint-disable */
// this is an auto generated file. This will be overwritten

export const onCreateUserProfile = /* GraphQL */ `
  subscription OnCreateUserProfile(
    $filter: ModelSubscriptionUserProfileFilterInput
  ) {
    onCreateUserProfile(filter: $filter) {
      id
      owner
      displayName
      email
      locale
      marketingOptIn
      createdAt
      updatedAt
      __typename
    }
  }
`;
export const onUpdateUserProfile = /* GraphQL */ `
  subscription OnUpdateUserProfile(
    $filter: ModelSubscriptionUserProfileFilterInput
  ) {
    onUpdateUserProfile(filter: $filter) {
      id
      owner
      displayName
      email
      locale
      marketingOptIn
      createdAt
      updatedAt
      __typename
    }
  }
`;
export const onDeleteUserProfile = /* GraphQL */ `
  subscription OnDeleteUserProfile(
    $filter: ModelSubscriptionUserProfileFilterInput
  ) {
    onDeleteUserProfile(filter: $filter) {
      id
      owner
      displayName
      email
      locale
      marketingOptIn
      createdAt
      updatedAt
      __typename
    }
  }
`;
export const onCreateLibraryItem = /* GraphQL */ `
  subscription OnCreateLibraryItem(
    $filter: ModelSubscriptionLibraryItemFilterInput
  ) {
    onCreateLibraryItem(filter: $filter) {
      id
      title
      compatibleClasses
      region
      standards
      version
      description
      hasActorCapability
      hasSensorCapability
      hasControllerCapability
      createdAt
      updatedAt
      __typename
    }
  }
`;
export const onUpdateLibraryItem = /* GraphQL */ `
  subscription OnUpdateLibraryItem(
    $filter: ModelSubscriptionLibraryItemFilterInput
  ) {
    onUpdateLibraryItem(filter: $filter) {
      id
      title
      compatibleClasses
      region
      standards
      version
      description
      hasActorCapability
      hasSensorCapability
      hasControllerCapability
      createdAt
      updatedAt
      __typename
    }
  }
`;
export const onDeleteLibraryItem = /* GraphQL */ `
  subscription OnDeleteLibraryItem(
    $filter: ModelSubscriptionLibraryItemFilterInput
  ) {
    onDeleteLibraryItem(filter: $filter) {
      id
      title
      compatibleClasses
      region
      standards
      version
      description
      hasActorCapability
      hasSensorCapability
      hasControllerCapability
      createdAt
      updatedAt
      __typename
    }
  }
`;
export const onCreateSmartHome = /* GraphQL */ `
  subscription OnCreateSmartHome(
    $filter: ModelSubscriptionSmartHomeFilterInput
  ) {
    onCreateSmartHome(filter: $filter) {
      id
      owners
      country
      zip
      streetCode
      houseNumber
      suffix
      address
      description
      ownerName
      createdAt
      updatedAt
      __typename
    }
  }
`;
export const onUpdateSmartHome = /* GraphQL */ `
  subscription OnUpdateSmartHome(
    $filter: ModelSubscriptionSmartHomeFilterInput
  ) {
    onUpdateSmartHome(filter: $filter) {
      id
      owners
      country
      zip
      streetCode
      houseNumber
      suffix
      address
      description
      ownerName
      createdAt
      updatedAt
      __typename
    }
  }
`;
export const onDeleteSmartHome = /* GraphQL */ `
  subscription OnDeleteSmartHome(
    $filter: ModelSubscriptionSmartHomeFilterInput
  ) {
    onDeleteSmartHome(filter: $filter) {
      id
      owners
      country
      zip
      streetCode
      houseNumber
      suffix
      address
      description
      ownerName
      createdAt
      updatedAt
      __typename
    }
  }
`;
export const onCreateSmartHomeDesign = /* GraphQL */ `
  subscription OnCreateSmartHomeDesign(
    $filter: ModelSubscriptionSmartHomeDesignFilterInput
  ) {
    onCreateSmartHomeDesign(filter: $filter) {
      id
      smartHomeId
      version
      lastModified
      lockedBy
      lockedAt
      ontologyVersion
      createdAt
      updatedAt
      __typename
    }
  }
`;
export const onUpdateSmartHomeDesign = /* GraphQL */ `
  subscription OnUpdateSmartHomeDesign(
    $filter: ModelSubscriptionSmartHomeDesignFilterInput
  ) {
    onUpdateSmartHomeDesign(filter: $filter) {
      id
      smartHomeId
      version
      lastModified
      lockedBy
      lockedAt
      ontologyVersion
      createdAt
      updatedAt
      __typename
    }
  }
`;
export const onDeleteSmartHomeDesign = /* GraphQL */ `
  subscription OnDeleteSmartHomeDesign(
    $filter: ModelSubscriptionSmartHomeDesignFilterInput
  ) {
    onDeleteSmartHomeDesign(filter: $filter) {
      id
      smartHomeId
      version
      lastModified
      lockedBy
      lockedAt
      ontologyVersion
      createdAt
      updatedAt
      __typename
    }
  }
`;
