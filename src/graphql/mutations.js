/* eslint-disable */
// this is an auto generated file. This will be overwritten

export const createUserProfile = /* GraphQL */ `
  mutation CreateUserProfile(
    $input: CreateUserProfileInput!
    $condition: ModelUserProfileConditionInput
  ) {
    createUserProfile(input: $input, condition: $condition) {
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
export const updateUserProfile = /* GraphQL */ `
  mutation UpdateUserProfile(
    $input: UpdateUserProfileInput!
    $condition: ModelUserProfileConditionInput
  ) {
    updateUserProfile(input: $input, condition: $condition) {
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
export const deleteUserProfile = /* GraphQL */ `
  mutation DeleteUserProfile(
    $input: DeleteUserProfileInput!
    $condition: ModelUserProfileConditionInput
  ) {
    deleteUserProfile(input: $input, condition: $condition) {
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
export const createLibraryItem = /* GraphQL */ `
  mutation CreateLibraryItem(
    $input: CreateLibraryItemInput!
    $condition: ModelLibraryItemConditionInput
  ) {
    createLibraryItem(input: $input, condition: $condition) {
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
export const updateLibraryItem = /* GraphQL */ `
  mutation UpdateLibraryItem(
    $input: UpdateLibraryItemInput!
    $condition: ModelLibraryItemConditionInput
  ) {
    updateLibraryItem(input: $input, condition: $condition) {
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
export const deleteLibraryItem = /* GraphQL */ `
  mutation DeleteLibraryItem(
    $input: DeleteLibraryItemInput!
    $condition: ModelLibraryItemConditionInput
  ) {
    deleteLibraryItem(input: $input, condition: $condition) {
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
export const createSmartHome = /* GraphQL */ `
  mutation CreateSmartHome(
    $input: CreateSmartHomeInput!
    $condition: ModelSmartHomeConditionInput
  ) {
    createSmartHome(input: $input, condition: $condition) {
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
export const updateSmartHome = /* GraphQL */ `
  mutation UpdateSmartHome(
    $input: UpdateSmartHomeInput!
    $condition: ModelSmartHomeConditionInput
  ) {
    updateSmartHome(input: $input, condition: $condition) {
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
export const deleteSmartHome = /* GraphQL */ `
  mutation DeleteSmartHome(
    $input: DeleteSmartHomeInput!
    $condition: ModelSmartHomeConditionInput
  ) {
    deleteSmartHome(input: $input, condition: $condition) {
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
export const createSmartHomeDesign = /* GraphQL */ `
  mutation CreateSmartHomeDesign(
    $input: CreateSmartHomeDesignInput!
    $condition: ModelSmartHomeDesignConditionInput
  ) {
    createSmartHomeDesign(input: $input, condition: $condition) {
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
export const updateSmartHomeDesign = /* GraphQL */ `
  mutation UpdateSmartHomeDesign(
    $input: UpdateSmartHomeDesignInput!
    $condition: ModelSmartHomeDesignConditionInput
  ) {
    updateSmartHomeDesign(input: $input, condition: $condition) {
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
export const deleteSmartHomeDesign = /* GraphQL */ `
  mutation DeleteSmartHomeDesign(
    $input: DeleteSmartHomeDesignInput!
    $condition: ModelSmartHomeDesignConditionInput
  ) {
    deleteSmartHomeDesign(input: $input, condition: $condition) {
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
